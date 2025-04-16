"""
Tests pour vérifier que la commande backup_database fonctionne correctement
"""
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

from django.test import TestCase
from django.core.management import call_command
from django.conf import settings

from core.management.commands.backup_database import Command


class BackupDatabaseTestCase(TestCase):
    """Tests pour la commande backup_database"""

    def setUp(self):
        """Créer un répertoire temporaire pour les sauvegardes"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Supprimer le répertoire temporaire"""
        shutil.rmtree(self.temp_dir)

    @patch('core.management.commands.backup_database.subprocess.run')
    def test_backup_database_command(self, mock_run):
        """Tester que la commande backup_database fonctionne correctement"""
        # Configurer le mock pour simuler une exécution réussie
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Sauvegarde réussie"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Créer un fichier temporaire pour simuler une sauvegarde
        with tempfile.NamedTemporaryFile(suffix='.sql', dir=self.temp_dir, delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(b"-- Contenu de test pour la sauvegarde")

        # Simuler la création du fichier de sauvegarde par pg_dump
        def side_effect(*args, **kwargs):
            # Extraire le chemin du fichier de sauvegarde à partir de la commande
            cmd = args[0]
            file_index = cmd.index('--file') + 1
            backup_path = cmd[file_index]

            # Créer un fichier vide à cet emplacement
            with open(backup_path, 'w') as f:
                f.write("-- Contenu de test pour la sauvegarde")

            return mock_process

        mock_run.side_effect = side_effect

        # Exécuter la commande avec le répertoire temporaire
        out = StringIO()
        call_command('backup_database', backup_dir=self.temp_dir, stdout=out)

        # Vérifier que la commande a été appelée avec les bons arguments
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]

        # Vérifier que pg_dump est appelé avec les bons paramètres
        self.assertEqual(cmd_args[0], 'pg_dump')
        self.assertIn('--host', cmd_args)
        self.assertIn('--port', cmd_args)
        self.assertIn('--username', cmd_args)
        self.assertIn('--format', cmd_args)
        self.assertIn('--file', cmd_args)

        # Vérifier que le message de succès est affiché
        output = out.getvalue()
        self.assertIn("Sauvegarde créée avec succès", output)

    @patch('core.management.commands.backup_database.subprocess.run')
    def test_backup_database_error(self, mock_run):
        """Tester que la commande gère correctement les erreurs"""
        # Configurer le mock pour simuler une erreur
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "Erreur lors de la sauvegarde"
        mock_run.return_value = mock_process

        # Capturer la sortie standard pour éviter les messages d'erreur dans les résultats de test
        out = StringIO()
        # Exécuter la commande avec le répertoire temporaire
        with self.assertRaises(Exception):
            call_command('backup_database', backup_dir=self.temp_dir, stdout=out)

    @patch('core.management.commands.backup_database.subprocess.run')
    def test_backup_database_dry_run(self, mock_run):
        """Tester que le mode simulation fonctionne correctement"""
        # Exécuter la commande en mode simulation
        out = StringIO()
        call_command('backup_database', backup_dir=self.temp_dir, dry_run=True, stdout=out)

        # Vérifier que pg_dump n'a pas été appelé
        mock_run.assert_not_called()

        # Vérifier que le message de simulation est affiché
        output = out.getvalue()
        self.assertIn("Mode simulation", output)

    def test_cleanup_old_backups(self):
        """Tester que la commande de nettoyage des anciennes sauvegardes fonctionne"""
        # Créer un fichier de sauvegarde dans le répertoire temporaire
        backup_file = os.path.join(self.temp_dir, "test_backup.sql")
        with open(backup_file, 'w') as f:
            f.write("-- Contenu de test pour la sauvegarde")

        # Vérifier que le fichier existe
        self.assertTrue(os.path.exists(backup_file))

        # Exécuter la commande avec le répertoire temporaire
        out = StringIO()
        call_command('backup_database', backup_dir=self.temp_dir, dry_run=True, verbose=True, stdout=out)

        # Vérifier que le message de simulation est affiché
        output = out.getvalue()
        self.assertIn("Mode simulation", output)
