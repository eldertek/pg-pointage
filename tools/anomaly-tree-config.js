// Conditions et actions prédéfinies avec descriptions
const CONDITIONS = [
  { id: "site_status", name: "Statut du site", description: "Vérifie si le site est actif ou inactif" },
  { id: "schedule_status", name: "Statut du planning", description: "Vérifie si le planning est actif ou inactif" },
  { id: "schedule_type", name: "Type de planning", description: "Vérifie si le planning est de type fixe ou fréquence" },
  { id: "employee_linked", name: "Employé lié au site", description: "Vérifie si l'employé est rattaché au site" },
  { id: "arrival_exists", name: "Présence pointage d'arrivée", description: "Vérifie si un pointage d'arrivée existe pour la journée" },
  { id: "departure_exists", name: "Présence pointage de départ", description: "Vérifie si un pointage de départ existe pour la journée" },
  { id: "arrival_time", name: "Heure d'arrivée vs planning", description: "Compare l'heure d'arrivée avec l'heure prévue dans le planning" },
  { id: "departure_time", name: "Heure de départ vs planning", description: "Compare l'heure de départ avec l'heure prévue dans le planning" },
  { id: "duration", name: "Durée de présence vs planning", description: "Compare la durée de présence avec la durée prévue dans le planning" },
  { id: "day_of_week", name: "Jour de la semaine", description: "Vérifie le jour de la semaine du pointage" },
  { id: "day_type", name: "Type de journée", description: "Vérifie si la journée est de type journée entière, matin ou après-midi" },
  { id: "processing_mode", name: "Mode de traitement", description: "Vérifie si le traitement est effectué en temps réel ou en batch" }
];

const ACTIONS = [
  { id: "none", name: "RAS", description: "Aucune action à effectuer" },
  { id: "late", name: "Créer anomalie LATE", description: "Crée une anomalie de retard" },
  { id: "early_departure", name: "Créer anomalie EARLY_DEPARTURE", description: "Crée une anomalie de départ anticipé" },
  { id: "missing_arrival", name: "Créer anomalie MISSING_ARRIVAL", description: "Crée une anomalie d'arrivée manquante" },
  { id: "missing_departure", name: "Créer anomalie MISSING_DEPARTURE", description: "Crée une anomalie de départ manquant" },
  { id: "insufficient_hours", name: "Créer anomalie INSUFFICIENT_HOURS", description: "Crée une anomalie d'heures insuffisantes" },
  { id: "consecutive_same_type", name: "Créer anomalie CONSECUTIVE_SAME_TYPE", description: "Crée une anomalie de pointages consécutifs du même type" },
  { id: "unlinked_schedule", name: "Créer anomalie UNLINKED_SCHEDULE", description: "Crée une anomalie de planning non lié" },
  { id: "other", name: "Créer anomalie OTHER", description: "Crée une anomalie de type autre" }
];

// Valeurs prédéfinies pour certaines conditions
const PREDEFINED_VALUES = {
  "site_status": ["Actif", "Inactif"],
  "schedule_status": ["Actif", "Inactif"],
  "schedule_type": ["FIXED", "FREQUENCY"],
  "employee_linked": ["Oui", "Non"],
  "arrival_exists": ["Oui", "Non"],
  "departure_exists": ["Oui", "Non"],
  "arrival_time": ["À l'heure", "En retard", "Très en retard"],
  "departure_time": ["À l'heure", "Départ anticipé", "Départ très anticipé"],
  "duration": ["Suffisante", "Insuffisante"],
  "day_of_week": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
  "day_type": ["FULL", "AM", "PM"],
  "processing_mode": ["Temps réel", "Batch"]
};

// Configuration des marges et tolérances
const DEFAULT_CONFIG = {
  late_margin: 15,
  early_departure_margin: 15,
  frequency_tolerance: 10,
  ambiguous_margin: 20
};

// Configuration du système de logging
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3
};

const LOG_CONFIG = {
  level: LOG_LEVELS.DEBUG, // Niveau de log minimum à afficher
  console: true,           // Afficher les logs dans la console
  display: true,           // Afficher les logs dans l'interface
  maxDisplayLogs: 100      // Nombre maximum de logs à afficher dans l'interface
};

let logHistory = [];

// Fonction de logging centralisée
function log(level, message, data = null) {
  if (level < LOG_CONFIG.level) return;

  const timestamp = new Date().toISOString();
  const levelNames = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
  const levelName = levelNames[level];

  // Formater le message
  let formattedMessage = `[${timestamp}] [${levelName}] ${message}`;

  // Ajouter les données si présentes
  let dataString = '';
  if (data !== null) {
    try {
      if (typeof data === 'object') {
        dataString = JSON.stringify(data, null, 2);
      } else {
        dataString = String(data);
      }
    } catch (e) {
      dataString = '[Impossible de sérialiser les données]';
    }
  }

  // Créer l'entrée de log complète
  const logEntry = {
    timestamp,
    level,
    levelName,
    message,
    data: dataString,
    formattedMessage: dataString ? `${formattedMessage}\n${dataString}` : formattedMessage
  };

  // Ajouter au historique
  logHistory.push(logEntry);
  if (logHistory.length > LOG_CONFIG.maxDisplayLogs) {
    logHistory.shift();
  }

  // Afficher dans la console si activé
  if (LOG_CONFIG.console) {
    const styles = {
      [LOG_LEVELS.DEBUG]: 'color: gray',
      [LOG_LEVELS.INFO]: 'color: blue',
      [LOG_LEVELS.WARN]: 'color: orange',
      [LOG_LEVELS.ERROR]: 'color: red; font-weight: bold'
    };

    console.log(`%c${formattedMessage}`, styles[level]);
    if (dataString) {
      console.log(data);
    }
  }

  // Afficher dans l'interface si activé
  if (LOG_CONFIG.display) {
    updateLogDisplay();
  }
}

// Fonctions de log par niveau
function logDebug(message, data = null) {
  log(LOG_LEVELS.DEBUG, message, data);
}

function logInfo(message, data = null) {
  log(LOG_LEVELS.INFO, message, data);
}

function logWarn(message, data = null) {
  log(LOG_LEVELS.WARN, message, data);
}

function logError(message, data = null) {
  log(LOG_LEVELS.ERROR, message, data);
}

// Mettre à jour l'affichage des logs dans l'interface
function updateLogDisplay() {
  const logContainer = document.getElementById('logContainer');
  if (!logContainer) return;

  // Limiter le nombre de logs affichés
  const logsToShow = logHistory.slice(-LOG_CONFIG.maxDisplayLogs);

  // Générer le HTML pour les logs
  let html = '';
  logsToShow.forEach(entry => {
    const bgColors = {
      [LOG_LEVELS.DEBUG]: '#f5f5f5',
      [LOG_LEVELS.INFO]: '#e3f2fd',
      [LOG_LEVELS.WARN]: '#fff3e0',
      [LOG_LEVELS.ERROR]: '#ffebee'
    };

    html += `<div class="log-entry" style="background-color: ${bgColors[entry.level]}; padding: 8px; margin-bottom: 4px; border-radius: 4px; font-family: monospace; white-space: pre-wrap;">
      <div><strong>${entry.levelName}</strong> - ${entry.timestamp}</div>
      <div>${entry.message}</div>
      ${entry.data ? `<div style="margin-top: 4px; padding-left: 12px; border-left: 2px solid #ccc;">${entry.data}</div>` : ''}
    </div>`;
  });

  logContainer.innerHTML = html;

  // Scroll vers le bas pour voir les derniers logs
  logContainer.scrollTop = logContainer.scrollHeight;
}

// Fonction pour effacer les logs
function clearLogs() {
  logHistory = [];
  updateLogDisplay();
  logInfo('Logs effacés');
}

let config = { ...DEFAULT_CONFIG };
let tree = null;

// Log initial
logInfo('Application démarrée', { version: '1.0', config: DEFAULT_CONFIG });

function renderTree() {
  logInfo('Rendu de l\'arbre de décision');

  const container = document.getElementById('treeContainer');
  container.innerHTML = '';

  if (!tree) {
    logInfo('Aucun arbre défini, affichage du message d\'aide');
    container.innerHTML = '<p style="color:#999">Aucun arbre défini. Cliquez sur "Nouvel arbre" pour commencer.</p>';
    return;
  }

  logDebug('Rendu de l\'arbre avec la structure', {
    condition: tree.condition,
    condition_id: tree.condition_id,
    branchesCount: tree.branches ? tree.branches.length : 0
  });

  container.appendChild(renderNode(tree, 0, []));
  logInfo('Rendu de l\'arbre terminé');
}

// Ajout d'une propriété d'état d'ouverture sur chaque noeud
function ensureAccordionState(node) {
  if (node && node.condition) {
    if (typeof node._open === 'undefined') node._open = true;
    if (Array.isArray(node.branches)) {
      node.branches.forEach(branch => {
        if (branch.children) ensureAccordionState(branch.children);
      });
    } else if (!node.branches) {
      // Initialiser les branches si elles n'existent pas
      node.branches = [];
    }
  }
}

function toggleAccordion(node) {
  node._open = !node._open;
  renderTree();
}

// Utilitaire pour retrouver un noeud/branche par chemin d'index
function getNodeByPath(node, path) {
  if (!path.length) return node;
  const [idx, ...rest] = path;

  // Vérifier si le noeud a des branches
  if (!node.branches || !node.branches[idx]) return null;

  // Si c'est le dernier élément du chemin, retourner la branche
  if (rest.length === 0) return node.branches[idx];

  // Sinon, continuer la recherche dans les enfants
  if (node.branches[idx].children) {
    return getNodeByPath(node.branches[idx].children, rest);
  }

  return null;
}

function renderNode(node, depth, path = []) {
  logDebug(`Rendu du noeud au chemin [${path.join(', ')}], profondeur ${depth}`, {
    nodeType: node ? (node.condition ? 'condition' : (node.action ? 'action' : 'autre')) : 'null',
    condition: node ? node.condition : null,
    condition_id: node ? node.condition_id : null
  });

  ensureAccordionState(node);
  const div = document.createElement('div');
  div.className = 'tree-node';

  // Condition
  if (node.condition) {
    // Accordéon : bouton ▶/▼
    const toggleBtn = document.createElement('span');
    toggleBtn.style.cursor = 'pointer';
    toggleBtn.style.fontWeight = 'bold';
    toggleBtn.style.marginRight = '8px';
    toggleBtn.textContent = node._open ? '▼' : '▶';
    toggleBtn.onclick = () => toggleAccordion(node);
    div.appendChild(toggleBtn);

    // Affichage de la condition avec tooltip
    const label = document.createElement('span');
    label.className = 'tree-label';
    label.textContent = node.condition;
    if (node.description) {
      label.title = node.description;
      label.style.cursor = 'help';
    }
    div.appendChild(label);

    // Affichage de la description en petit
    if (node.description && node._open) {
      const descDiv = document.createElement('div');
      descDiv.className = 'tree-description';
      descDiv.textContent = node.description;
      div.appendChild(descDiv);
    }

    logDebug(`Noeud de condition rendu: ${node.condition}`, {
      isOpen: node._open,
      branchesCount: node.branches ? node.branches.length : 0
    });

    if (node._open) {
      node.branches.forEach((branch, idx) => {
        const branchDiv = document.createElement('div');
        branchDiv.className = 'tree-branch';
        branchDiv.style.marginLeft = '24px';
        branchDiv.style.borderLeft = '1.5px dashed #c7d0e0';
        branchDiv.style.paddingLeft = '12px';
        branchDiv.style.background = depth % 2 === 1 ? '#f7f9fb' : 'none';

        // Valeur de la branche
        const valueSpan = document.createElement('span');
        valueSpan.className = 'branch-value';
        valueSpan.textContent = branch.value;
        branchDiv.appendChild(valueSpan);

        // Action ou sous-arbre
        if (branch.action) {
          const actionSpan = document.createElement('span');
          actionSpan.className = 'tree-action';
          actionSpan.innerHTML = `→ ${branch.action}`;
          if (branch.action_description) {
            actionSpan.title = branch.action_description;
            actionSpan.style.cursor = 'help';
          }
          branchDiv.appendChild(actionSpan);

          // Description de l'action en petit
          if (branch.action_description) {
            const actionDescDiv = document.createElement('div');
            actionDescDiv.className = 'action-description';
            actionDescDiv.textContent = branch.action_description;
            branchDiv.appendChild(actionDescDiv);
          }
        } else if (branch.children) {
          branchDiv.appendChild(renderNode(branch.children, depth + 1, [...path, idx]));
        }

        // Contrôles pour chaque branche
        const controls = document.createElement('span');
        controls.className = 'tree-controls';
        controls.innerHTML = `
          <button onclick="editBranchAtPath([${[...path, idx]}])" title="Modifier la valeur de cette branche">Éditer</button>
          <button class='delete' onclick="deleteBranchAtPath([${[...path, idx]}])" title="Supprimer cette branche et tous ses enfants">Supprimer</button>
          <button onclick="addChildConditionAtPath([${[...path, idx]}])" title="Ajouter une condition enfant à cette branche">Ajouter sous-condition</button>
          <button onclick="addActionAtPath([${[...path, idx]}])" title="Ajouter une action à cette branche">Ajouter action</button>
        `;
        branchDiv.appendChild(controls);
        div.appendChild(branchDiv);
      });

      // Ajouter une branche
      const addBranchBtn = document.createElement('button');
      addBranchBtn.textContent = 'Ajouter une branche';
      addBranchBtn.title = 'Ajouter une nouvelle branche à cette condition';
      addBranchBtn.onclick = () => addBranchAtPath(path);
      div.appendChild(addBranchBtn);
    }
  } else if (node.action) {
    div.innerHTML = `<span class='tree-action'>${node.action}</span>`;
    if (node.action_description) {
      div.innerHTML += `<div class='action-description'>${node.action_description}</div>`;
    }
  }

  // Contrôle pour supprimer la condition racine
  if (depth === 0 && tree) {
    const delBtn = document.createElement('button');
    delBtn.textContent = 'Supprimer l\'arbre';
    delBtn.className = 'delete';
    delBtn.title = 'Supprimer complètement cet arbre de décision';
    delBtn.onclick = () => { tree = null; renderTree(); };
    div.appendChild(delBtn);
  }

  return div;
}

// Gestion de la modale
let modalCallback = null;
let modalContext = {};

function openModal({ title, fields, initial = {}, onSubmit }) {
  document.getElementById('modalTitle').textContent = title;
  const modalFields = document.getElementById('modalFields');
  modalFields.innerHTML = '';
  fields.forEach(field => {
    let html = '';
    if (field.type === 'select') {
      html = `<label>${field.label}<br><select name="${field.name}" style="width:100%;margin-top:4px;">`;
      field.options.forEach(opt => {
        let optValue, optText;
        if (typeof opt === 'object') {
          optValue = opt.id;
          optText = opt.name;
          const selected = initial[field.name] === optValue ? 'selected' : '';
          html += `<option value="${optValue}" ${selected} title="${opt.description || ''}">${optText}</option>`;
        } else {
          optValue = optText = opt;
          const selected = initial[field.name] === optValue ? 'selected' : '';
          html += `<option value="${optValue}" ${selected}>${optText}</option>`;
        }
      });
      html += '</select></label>';
      if (field.description) {
        html += `<div style="font-size:0.85em;color:#666;margin-top:4px;">${field.description}</div>`;
      }
    } else if (field.type === 'text') {
      html = `<label>${field.label}<br><input type="text" name="${field.name}" value="${initial[field.name]||''}" style="width:100%;margin-top:4px;"></label>`;
      if (field.description) {
        html += `<div style="font-size:0.85em;color:#666;margin-top:4px;">${field.description}</div>`;
      }
    } else if (field.type === 'number') {
      html = `<label>${field.label}<br><input type="number" name="${field.name}" value="${initial[field.name]||''}" min="${field.min || 0}" max="${field.max || 999}" style="width:100%;margin-top:4px;"></label>`;
      if (field.description) {
        html += `<div style="font-size:0.85em;color:#666;margin-top:4px;">${field.description}</div>`;
      }
    }
    modalFields.innerHTML += `<div style="margin-bottom:16px;">${html}</div>`;
  });
  modalCallback = onSubmit;
  document.getElementById('modalOverlay').style.display = '';
  document.getElementById('editModal').style.display = '';
}

function closeModal() {
  document.getElementById('modalOverlay').style.display = 'none';
  document.getElementById('editModal').style.display = 'none';
  modalCallback = null;
}

document.getElementById('modalForm').onsubmit = function(e) {
  e.preventDefault();
  const data = {};
  Array.from(e.target.elements).forEach(el => {
    if (el.name) data[el.name] = el.value;
  });
  if (modalCallback) modalCallback(data);
  closeModal();
};

// Remplacement des prompt par modale
function addRootCondition() {
  logInfo('Ouverture de la modale pour créer une nouvelle condition racine');

  openModal({
    title: 'Nouvelle condition racine',
    fields: [
      {
        type: 'select',
        name: 'condition',
        label: 'Condition',
        options: CONDITIONS,
        description: 'Sélectionnez la condition racine de votre arbre de décision'
      }
    ],
    onSubmit: (data) => {
      logInfo('Création d\'une nouvelle condition racine', { condition_id: data.condition });

      // Trouver l'objet condition complet
      const conditionObj = CONDITIONS.find(c => c.id === data.condition);
      if (!conditionObj) {
        logWarn('Condition non trouvée dans la liste des conditions prédéfinies', { condition_id: data.condition });
      }

      tree = {
        condition_id: data.condition,
        condition: conditionObj ? conditionObj.name : data.condition,
        description: conditionObj ? conditionObj.description : '',
        branches: []
      };

      logDebug('Nouvel arbre créé', tree);
      renderTree();
    }
  });
}

function addBranchAtPath(path) {
  logInfo('Ajout d\'une branche au chemin', { path });

  const node = getNodeByPath(tree, path);
  logDebug('Noeud récupéré', { node, path });

  // Vérifier si le noeud existe
  if (!node) {
    logError('Noeud non trouvé pour le chemin', { path });
    alert('Impossible de trouver le noeud. Veuillez réessayer.');
    return;
  }

  // Vérifier s'il y a des valeurs prédéfinies pour cette condition
  const conditionId = node.condition_id;
  const predefinedValues = PREDEFINED_VALUES[conditionId] || [];
  logDebug('Valeurs prédéfinies pour la condition', {
    conditionId,
    condition: node.condition,
    predefinedValues,
    hasPredefinedValues: predefinedValues.length > 0
  });

  const fields = [];
  if (predefinedValues.length > 0) {
    fields.push({
      type: 'select',
      name: 'value',
      label: 'Valeur de la branche',
      options: predefinedValues,
      description: `Sélectionnez une valeur pour la condition "${node.condition}"`
    });
  } else {
    fields.push({
      type: 'text',
      name: 'value',
      label: 'Valeur de la branche (ex: Actif, Inactif, Oui, Non, etc.)',
      description: `Entrez une valeur pour la condition "${node.condition}"`
    });
  }

  logInfo('Ouverture de la modale pour ajouter une branche', { condition: node.condition });
  openModal({
    title: 'Nouvelle branche',
    fields: fields,
    onSubmit: (data) => {
      logInfo('Soumission du formulaire pour ajouter une branche', { value: data.value });

      // S'assurer que branches est un tableau
      if (!node.branches) {
        logDebug('Initialisation du tableau de branches', { nodeId: node.condition_id });
        node.branches = [];
      }

      // Vérifier si la valeur existe déjà
      const valueExists = node.branches.some(branch => branch.value === data.value);
      if (valueExists) {
        logWarn('Tentative d\'ajout d\'une valeur en double', { value: data.value, condition: node.condition });
        alert(`La valeur "${data.value}" existe déjà pour cette condition. Veuillez choisir une autre valeur.`);
        return;
      }

      logInfo('Ajout d\'une nouvelle branche', { value: data.value, condition: node.condition });
      node.branches.push({ value: data.value });
      logDebug('Structure de l\'arbre après ajout', { tree });
      renderTree();
    }
  });
}

function editBranchAtPath(path) {
  logInfo('Modification d\'une branche au chemin', { path });

  const parentPath = path.slice(0, -1);
  const idx = path[path.length - 1];
  logDebug('Chemin décomposé', { parentPath, branchIndex: idx });

  const parent = getNodeByPath(tree, parentPath);
  logDebug('Noeud parent récupéré', { parent, parentPath });

  // Vérifier si le parent et ses branches existent
  if (!parent || !parent.branches || !parent.branches[idx]) {
    logError('Branche introuvable pour édition', { path, parentPath, idx });
    alert('Impossible de trouver la branche à éditer. Veuillez réessayer.');
    return;
  }

  const branch = parent.branches[idx];
  logDebug('Branche à éditer', { branch, index: idx });

  // Vérifier s'il y a des valeurs prédéfinies pour cette condition
  const conditionId = parent.condition_id;
  const predefinedValues = PREDEFINED_VALUES[conditionId] || [];
  logDebug('Valeurs prédéfinies pour la condition', {
    conditionId,
    condition: parent.condition,
    predefinedValues,
    hasPredefinedValues: predefinedValues.length > 0
  });

  const fields = [];
  if (predefinedValues.length > 0) {
    fields.push({
      type: 'select',
      name: 'value',
      label: 'Nouvelle valeur de la branche',
      options: predefinedValues,
      description: `Modifiez la valeur pour la condition "${parent.condition}"`
    });
  } else {
    fields.push({
      type: 'text',
      name: 'value',
      label: 'Nouvelle valeur de la branche',
      description: `Modifiez la valeur pour la condition "${parent.condition}"`
    });
  }

  logInfo('Ouverture de la modale pour éditer une branche', {
    branchValue: branch.value,
    condition: parent.condition
  });

  openModal({
    title: 'Éditer la branche',
    fields: fields,
    initial: { value: branch.value || '' },
    onSubmit: (data) => {
      logInfo('Soumission du formulaire pour éditer une branche', {
        oldValue: branch.value,
        newValue: data.value
      });

      // Vérifier si la nouvelle valeur existe déjà dans d'autres branches
      const valueExistsElsewhere = parent.branches.some((b, i) =>
        i !== idx && b.value === data.value
      );

      if (valueExistsElsewhere) {
        logWarn('Tentative de modification vers une valeur en double', {
          value: data.value,
          condition: parent.condition
        });
        alert(`La valeur "${data.value}" existe déjà pour cette condition. Veuillez choisir une autre valeur.`);
        return;
      }

      logInfo('Modification de la valeur d\'une branche', {
        oldValue: branch.value,
        newValue: data.value,
        path
      });

      branch.value = data.value;
      logDebug('Structure de l\'arbre après modification', { tree });
      renderTree();
    }
  });
}

function deleteBranchAtPath(path) {
  logInfo('Suppression d\'une branche au chemin', { path });

  const parentPath = path.slice(0, -1);
  const idx = path[path.length - 1];
  logDebug('Chemin décomposé', { parentPath, branchIndex: idx });

  const parent = getNodeByPath(tree, parentPath);
  logDebug('Noeud parent récupéré', { parent, parentPath });

  // Vérifier si le parent et ses branches existent
  if (!parent || !parent.branches || !parent.branches[idx]) {
    logError('Branche introuvable pour suppression', { path, parentPath, idx });
    alert('Impossible de trouver la branche à supprimer. Veuillez réessayer.');
    return;
  }

  const branchToDelete = parent.branches[idx];
  logDebug('Branche à supprimer', { branch: branchToDelete, index: idx });

  // Vérifier si la branche a des enfants ou des actions
  const hasChildren = branchToDelete.children ? true : false;
  const hasAction = branchToDelete.action ? true : false;

  let confirmMessage = 'Supprimer cette branche ?';
  if (hasChildren) {
    confirmMessage = 'Cette branche contient des sous-conditions qui seront également supprimées. Continuer ?';
  } else if (hasAction) {
    confirmMessage = 'Cette branche contient une action qui sera supprimée. Continuer ?';
  }

  logInfo('Demande de confirmation pour suppression', {
    hasChildren,
    hasAction,
    value: branchToDelete.value
  });

  if (confirm(confirmMessage)) {
    logInfo('Suppression confirmée de la branche', {
      value: branchToDelete.value,
      path,
      hasChildren,
      hasAction
    });

    parent.branches.splice(idx, 1);
    logDebug('Structure de l\'arbre après suppression', { tree });
    renderTree();
  } else {
    logInfo('Suppression annulée par l\'utilisateur');
  }
}

function addChildConditionAtPath(path) {
  logInfo('Ajout d\'une sous-condition au chemin', { path });

  const branch = getNodeByPath(tree, path);
  logDebug('Branche récupérée', { branch, path });

  // Vérifier si la branche existe
  if (!branch) {
    logError('Branche introuvable pour ajout de sous-condition', { path });
    alert('Impossible de trouver la branche. Veuillez réessayer.');
    return;
  }

  // Vérifier si la branche a déjà une sous-condition
  if (branch.children) {
    logWarn('La branche a déjà une sous-condition', {
      path,
      existingCondition: branch.children.condition
    });
  }

  // Vérifier si la branche a déjà une action
  if (branch.action) {
    logWarn('La branche a déjà une action qui sera supprimée', {
      path,
      existingAction: branch.action
    });
  }

  logInfo('Ouverture de la modale pour ajouter une sous-condition', { branchValue: branch.value });
  openModal({
    title: 'Nouvelle sous-condition',
    fields: [
      {
        type: 'select',
        name: 'condition',
        label: 'Condition',
        options: CONDITIONS,
        description: 'Sélectionnez une condition pour cette branche'
      }
    ],
    onSubmit: (data) => {
      logInfo('Soumission du formulaire pour ajouter une sous-condition', { condition_id: data.condition });

      // Trouver l'objet condition complet
      const conditionObj = CONDITIONS.find(c => c.id === data.condition);
      if (!conditionObj) {
        logWarn('Condition non trouvée dans la liste des conditions prédéfinies', { condition_id: data.condition });
      }

      // S'assurer que nous n'avons pas à la fois children et branches
      if (branch.branches) {
        logDebug('Suppression des branches existantes pour éviter les conflits', {
          branchesCount: branch.branches.length
        });
        delete branch.branches;
      }

      // Supprimer l'action si elle existe pour éviter les conflits
      if (branch.action) {
        logDebug('Suppression de l\'action existante pour éviter les conflits', {
          action: branch.action,
          action_id: branch.action_id
        });
        delete branch.action;
        delete branch.action_id;
        delete branch.action_description;
      }

      logInfo('Création d\'une nouvelle sous-condition', {
        condition_id: data.condition,
        condition: conditionObj ? conditionObj.name : data.condition
      });

      branch.children = {
        condition_id: data.condition,
        condition: conditionObj ? conditionObj.name : data.condition,
        description: conditionObj ? conditionObj.description : '',
        branches: []
      };

      logDebug('Structure de l\'arbre après ajout de sous-condition', { tree });
      renderTree();
    }
  });
}

function addActionAtPath(path) {
  logInfo('Ajout d\'une action au chemin', { path });

  const branch = getNodeByPath(tree, path);
  logDebug('Branche récupérée', { branch, path });

  // Vérifier si la branche existe
  if (!branch) {
    logError('Branche introuvable pour ajout d\'action', { path });
    alert('Impossible de trouver la branche. Veuillez réessayer.');
    return;
  }

  // Vérifier si la branche a déjà une action
  if (branch.action) {
    logWarn('La branche a déjà une action qui sera remplacée', {
      path,
      existingAction: branch.action
    });
  }

  // Vérifier si la branche a déjà des sous-conditions
  if (branch.children) {
    logWarn('La branche a déjà des sous-conditions qui seront supprimées', {
      path,
      existingCondition: branch.children.condition
    });
  }

  logInfo('Ouverture de la modale pour ajouter une action', { branchValue: branch.value });
  openModal({
    title: 'Nouvelle action',
    fields: [
      {
        type: 'select',
        name: 'action',
        label: 'Action à effectuer',
        options: ACTIONS,
        description: 'Sélectionnez l\'action à effectuer pour cette branche'
      }
    ],
    onSubmit: (data) => {
      logInfo('Soumission du formulaire pour ajouter une action', { action_id: data.action });

      // Trouver l'objet action complet
      const actionObj = ACTIONS.find(a => a.id === data.action);
      if (!actionObj) {
        logWarn('Action non trouvée dans la liste des actions prédéfinies', { action_id: data.action });
      }

      // Supprimer les enfants s'ils existent pour éviter les conflits
      if (branch.children) {
        logDebug('Suppression des sous-conditions existantes pour éviter les conflits', {
          condition: branch.children.condition
        });
        delete branch.children;
      }

      logInfo('Ajout d\'une nouvelle action', {
        action_id: data.action,
        action: actionObj ? actionObj.name : data.action
      });

      branch.action_id = data.action;
      branch.action = actionObj ? actionObj.name : data.action;
      branch.action_description = actionObj ? actionObj.description : '';

      logDebug('Structure de l\'arbre après ajout d\'action', { tree });
      renderTree();
    }
  });
}

function configureSettings() {
  logInfo('Ouverture de la modale de configuration des marges et tolérances');
  logDebug('Configuration actuelle', config);

  openModal({
    title: 'Configuration des marges et tolérances',
    fields: [
      {
        type: 'number',
        name: 'late_margin',
        label: 'Marge de retard (minutes)',
        min: 0,
        max: 60,
        description: 'Nombre de minutes de tolérance pour les retards'
      },
      {
        type: 'number',
        name: 'early_departure_margin',
        label: 'Marge de départ anticipé (minutes)',
        min: 0,
        max: 60,
        description: 'Nombre de minutes de tolérance pour les départs anticipés'
      },
      {
        type: 'number',
        name: 'frequency_tolerance',
        label: 'Tolérance de fréquence (%)',
        min: 0,
        max: 100,
        description: 'Pourcentage de tolérance pour la durée des plannings fréquence'
      },
      {
        type: 'number',
        name: 'ambiguous_margin',
        label: 'Marge pour cas ambigus (minutes)',
        min: 0,
        max: 60,
        description: 'Marge de temps pour déterminer les cas ambigus'
      }
    ],
    initial: config,
    onSubmit: (data) => {
      logInfo('Soumission du formulaire de configuration', data);

      // Sauvegarder les anciennes valeurs pour le log
      const oldConfig = { ...config };

      // Convertir les valeurs en nombres
      config.late_margin = parseInt(data.late_margin) || DEFAULT_CONFIG.late_margin;
      config.early_departure_margin = parseInt(data.early_departure_margin) || DEFAULT_CONFIG.early_departure_margin;
      config.frequency_tolerance = parseInt(data.frequency_tolerance) || DEFAULT_CONFIG.frequency_tolerance;
      config.ambiguous_margin = parseInt(data.ambiguous_margin) || DEFAULT_CONFIG.ambiguous_margin;

      logInfo('Configuration mise à jour', {
        oldConfig,
        newConfig: { ...config }
      });

      alert('Configuration enregistrée avec succès.');
    }
  });
}

function exportTree() {
  logInfo('Tentative d\'export de l\'arbre de décision');

  if (!tree) {
    logWarn('Tentative d\'export sans arbre défini');
    alert('Aucun arbre à exporter.');
    return;
  }

  // Créer un objet d'export avec les métadonnées
  const exportData = {
    version: '1.0',
    date: new Date().toISOString(),
    config: { ...config },
    tree: tree
  };

  logInfo('Préparation des données pour l\'export', {
    version: exportData.version,
    date: exportData.date,
    configKeys: Object.keys(exportData.config)
  });
  logDebug('Données complètes pour l\'export', exportData);

  try {
    const jsonData = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'anomaly_tree_config.json';

    logInfo('Téléchargement du fichier d\'export', {
      filename: 'anomaly_tree_config.json',
      size: jsonData.length
    });

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    logInfo('Export réussi');
  } catch (error) {
    logError('Erreur lors de l\'export', { error: error.message, stack: error.stack });
    alert(`Erreur lors de l'export: ${error.message}`);
  }
}

function importTree() {
  logInfo('Ouverture de la boîte de dialogue pour importer un fichier');
  document.getElementById('importFile').click();
}

function validateTreeStructure(node) {
  logDebug('Validation de la structure d\'un noeud', { nodeType: node ? (node.condition ? 'condition' : 'autre') : 'null' });

  // Vérifier si le noeud est valide
  if (!node) {
    logWarn('Noeud invalide (null ou undefined)');
    return false;
  }

  // Vérifier si c'est une condition
  if (node.condition) {
    // Ajouter condition_id s'il manque
    if (!node.condition_id) {
      logWarn('condition_id manquant, tentative de récupération', { condition: node.condition });

      // Essayer de trouver l'ID correspondant au nom de la condition
      const conditionObj = CONDITIONS.find(c => c.name === node.condition);
      if (conditionObj) {
        logInfo('condition_id récupéré à partir du nom', {
          condition: node.condition,
          condition_id: conditionObj.id
        });
        node.condition_id = conditionObj.id;
      } else {
        // Utiliser un ID par défaut
        logWarn('Impossible de trouver l\'ID de la condition, utilisation de l\'ID par défaut', {
          condition: node.condition,
          default_id: 'site_status'
        });
        node.condition_id = 'site_status';
      }
    }

    // Ajouter description si elle manque
    if (!node.description) {
      logWarn('Description manquante, tentative de récupération', { condition_id: node.condition_id });

      const conditionObj = CONDITIONS.find(c => c.id === node.condition_id);
      if (conditionObj) {
        logInfo('Description récupérée à partir de l\'ID', {
          condition_id: node.condition_id,
          description: conditionObj.description
        });
        node.description = conditionObj.description;
      } else {
        logWarn('Impossible de trouver la description de la condition');
      }
    }

    // Vérifier si branches existe et est un tableau
    if (!Array.isArray(node.branches)) {
      logWarn('Branches non définies ou non valides, initialisation d\'un tableau vide', {
        branchesType: typeof node.branches
      });
      node.branches = [];
    }

    // Vérifier récursivement chaque branche
    let isValid = true;
    node.branches.forEach((branch, index) => {
      logDebug(`Validation de la branche ${index}`, { branch });

      // Vérifier si la branche a une valeur
      if (!branch.value) {
        logWarn(`Branche ${index} sans valeur, utilisation d'une valeur par défaut`);
        branch.value = 'Valeur par défaut';
      }

      // Supprimer les branches au même niveau que children
      if (branch.children && branch.branches) {
        logWarn(`Branche ${index} avec à la fois children et branches, suppression de branches`, {
          childrenCondition: branch.children.condition
        });
        delete branch.branches;
      }

      // Vérifier si la branche a une action
      if (branch.action && !branch.action_id) {
        logWarn(`Branche ${index} avec action mais sans action_id, tentative de récupération`, {
          action: branch.action
        });

        // Essayer de trouver l'ID correspondant au nom de l'action
        const actionObj = ACTIONS.find(a => a.name === branch.action);
        if (actionObj) {
          logInfo(`action_id récupéré pour la branche ${index}`, {
            action: branch.action,
            action_id: actionObj.id
          });
          branch.action_id = actionObj.id;
          branch.action_description = actionObj.description;
        } else {
          logWarn(`Impossible de trouver l'ID de l'action pour la branche ${index}`);
        }
      }

      // Vérifier si la branche a des enfants
      if (branch.children) {
        logDebug(`Validation récursive des enfants de la branche ${index}`);
        const childValid = validateTreeStructure(branch.children);
        if (!childValid) {
          logWarn(`Structure invalide dans les enfants de la branche ${index}`);
          isValid = false;
        }
      }
    });

    return isValid;
  }

  return true;
}

function handleImport(event) {
  logInfo('Traitement du fichier importé');

  const file = event.target.files[0];
  if (!file) {
    logWarn('Aucun fichier sélectionné pour l\'import');
    return;
  }

  logInfo('Lecture du fichier', {
    name: file.name,
    size: file.size,
    type: file.type
  });

  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      logDebug('Contenu du fichier lu', { contentLength: e.target.result.length });
      const data = JSON.parse(e.target.result);
      logDebug('Données JSON parsées', {
        hasTree: !!data.tree,
        hasConfig: !!data.config,
        version: data.version || 'non spécifiée'
      });

      // Vérifier si c'est un format ancien (juste l'arbre) ou nouveau (avec métadonnées)
      if (data.tree && data.config) {
        // Nouveau format
        logInfo('Format de fichier détecté: nouveau format avec métadonnées');

        const isValid = validateTreeStructure(data.tree);
        if (isValid) {
          logInfo('Structure de l\'arbre valide');
          tree = data.tree;

          // Sauvegarder l'ancienne configuration pour le log
          const oldConfig = { ...config };
          config = { ...DEFAULT_CONFIG, ...data.config };

          logInfo('Configuration mise à jour', {
            oldConfig,
            newConfig: config,
            version: data.version || 'inconnue'
          });

          alert(`Configuration importée avec succès (version ${data.version || 'inconnue'})`);
        } else {
          logWarn('Structure de l\'arbre invalide, des corrections ont été appliquées');
          tree = data.tree;

          // Sauvegarder l'ancienne configuration pour le log
          const oldConfig = { ...config };
          config = { ...DEFAULT_CONFIG, ...data.config };

          logInfo('Configuration mise à jour malgré la structure invalide', {
            oldConfig,
            newConfig: config
          });

          alert('Structure de l\'arbre invalide. Des corrections automatiques ont été appliquées.');
        }
      } else {
        // Ancien format (juste l'arbre)
        logInfo('Format de fichier détecté: ancien format (arbre uniquement)');

        const isValid = validateTreeStructure(data);
        if (isValid) {
          logInfo('Structure de l\'arbre valide (format ancien)');
          tree = data;
          alert('Arbre importé avec succès (format ancien)');
        } else {
          logWarn('Structure de l\'arbre invalide (format ancien), des corrections ont été appliquées');
          tree = data;
          alert('Structure de l\'arbre invalide. Des corrections automatiques ont été appliquées.');
        }
      }

      logInfo('Rendu de l\'arbre après import');
      renderTree();
    } catch (err) {
      logError('Erreur lors du parsing du fichier importé', {
        error: err.message,
        stack: err.stack
      });
      alert('Erreur lors de l\'import : ' + err.message);
    }
  };

  reader.onerror = function(e) {
    logError('Erreur lors de la lecture du fichier', { error: e.target.error });
    alert('Erreur lors de la lecture du fichier.');
  };

  reader.readAsText(file);
}

// Fonction pour créer un exemple d'arbre de décision
function createExampleTree() {
  logInfo('Tentative de création d\'un exemple d\'arbre de décision');

  if (tree) {
    logWarn('Un arbre existe déjà, demande de confirmation pour le remplacement');
    if (!confirm('Cela va remplacer l\'arbre actuel. Continuer ?')) {
      logInfo('Création de l\'exemple annulée par l\'utilisateur');
      return;
    }
    logInfo('Remplacement de l\'arbre existant confirmé');
  }

  logInfo('Création d\'un exemple d\'arbre de décision');

  // Créer un exemple d'arbre de décision
  tree = {
    condition_id: 'site_status',
    condition: 'Statut du site',
    description: 'Vérifie si le site est actif ou inactif',
    branches: [
      {
        value: 'Actif',
        children: {
          condition_id: 'employee_linked',
          condition: 'Employé lié au site',
          description: 'Vérifie si l\'employé est rattaché au site',
          branches: [
            {
              value: 'Non',
              action_id: 'unlinked_schedule',
              action: 'Créer anomalie UNLINKED_SCHEDULE',
              action_description: 'Crée une anomalie de planning non lié'
            },
            {
              value: 'Oui',
              children: {
                condition_id: 'schedule_type',
                condition: 'Type de planning',
                description: 'Vérifie si le planning est de type fixe ou fréquence',
                branches: [
                  {
                    value: 'FIXED',
                    children: {
                      condition_id: 'arrival_time',
                      condition: 'Heure d\'arrivée vs planning',
                      description: 'Compare l\'heure d\'arrivée avec l\'heure prévue dans le planning',
                      branches: [
                        {
                          value: 'À l\'heure',
                          action_id: 'none',
                          action: 'RAS',
                          action_description: 'Aucune action à effectuer'
                        },
                        {
                          value: 'En retard',
                          action_id: 'late',
                          action: 'Créer anomalie LATE',
                          action_description: 'Crée une anomalie de retard'
                        }
                      ]
                    }
                  },
                  {
                    value: 'FREQUENCY',
                    children: {
                      condition_id: 'duration',
                      condition: 'Durée de présence vs planning',
                      description: 'Compare la durée de présence avec la durée prévue dans le planning',
                      branches: [
                        {
                          value: 'Suffisante',
                          action_id: 'none',
                          action: 'RAS',
                          action_description: 'Aucune action à effectuer'
                        },
                        {
                          value: 'Insuffisante',
                          action_id: 'insufficient_hours',
                          action: 'Créer anomalie INSUFFICIENT_HOURS',
                          action_description: 'Crée une anomalie d\'heures insuffisantes'
                        }
                      ]
                    }
                  }
                ]
              }
            }
          ]
        }
      },
      {
        value: 'Inactif',
        action_id: 'none',
        action: 'RAS',
        action_description: 'Aucune action à effectuer'
      }
    ]
  };

  logDebug('Structure de l\'exemple d\'arbre créé', tree);
  logInfo('Rendu de l\'exemple d\'arbre');
  renderTree();

  logInfo('Exemple d\'arbre de décision créé avec succès');
  alert('Exemple d\'arbre de décision créé avec succès !');
}

// Initial render
renderTree();