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

let config = { ...DEFAULT_CONFIG };
let tree = null;

function renderTree() {
  const container = document.getElementById('treeContainer');
  container.innerHTML = '';
  if (!tree) {
    container.innerHTML = '<p style="color:#999">Aucun arbre défini. Cliquez sur "Nouvel arbre" pour commencer.</p>';
    return;
  }
  container.appendChild(renderNode(tree, 0, []));
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
  if (!node.branches || !node.branches[idx]) return null;
  if (rest.length === 0) return node.branches[idx];
  if (node.branches[idx].children) return getNodeByPath(node.branches[idx].children, rest);
  return null;
}

function renderNode(node, depth, path = []) {
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
      // Trouver l'objet condition complet
      const conditionObj = CONDITIONS.find(c => c.id === data.condition);
      tree = {
        condition_id: data.condition,
        condition: conditionObj ? conditionObj.name : data.condition,
        description: conditionObj ? conditionObj.description : '',
        branches: []
      };
      renderTree();
    }
  });
}

function addBranchAtPath(path) {
  const node = getNodeByPath(tree, path);
  // Vérifier s'il y a des valeurs prédéfinies pour cette condition
  const conditionId = node.condition_id;
  const predefinedValues = PREDEFINED_VALUES[conditionId] || [];

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

  openModal({
    title: 'Nouvelle branche',
    fields: fields,
    onSubmit: (data) => {
      if (!node.branches) node.branches = [];
      node.branches.push({ value: data.value });
      renderTree();
    }
  });
}

function editBranchAtPath(path) {
  const parentPath = path.slice(0, -1);
  const idx = path[path.length - 1];
  const parent = getNodeByPath(tree, parentPath);
  const branch = parent.branches[idx];

  // Vérifier s'il y a des valeurs prédéfinies pour cette condition
  const conditionId = parent.condition_id;
  const predefinedValues = PREDEFINED_VALUES[conditionId] || [];

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

  openModal({
    title: 'Éditer la branche',
    fields: fields,
    initial: { value: branch.value },
    onSubmit: (data) => {
      branch.value = data.value;
      renderTree();
    }
  });
}

function deleteBranchAtPath(path) {
  const parentPath = path.slice(0, -1);
  const idx = path[path.length - 1];
  const parent = getNodeByPath(tree, parentPath);
  if (confirm('Supprimer cette branche ?')) {
    parent.branches.splice(idx, 1);
    renderTree();
  }
}

function addChildConditionAtPath(path) {
  const branch = getNodeByPath(tree, path);
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
      // Trouver l'objet condition complet
      const conditionObj = CONDITIONS.find(c => c.id === data.condition);
      branch.children = {
        condition_id: data.condition,
        condition: conditionObj ? conditionObj.name : data.condition,
        description: conditionObj ? conditionObj.description : '',
        branches: []
      };
      renderTree();
    }
  });
}

function addActionAtPath(path) {
  const branch = getNodeByPath(tree, path);
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
      // Trouver l'objet action complet
      const actionObj = ACTIONS.find(a => a.id === data.action);
      branch.action_id = data.action;
      branch.action = actionObj ? actionObj.name : data.action;
      branch.action_description = actionObj ? actionObj.description : '';
      renderTree();
    }
  });
}

function configureSettings() {
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
      // Convertir les valeurs en nombres
      config.late_margin = parseInt(data.late_margin) || DEFAULT_CONFIG.late_margin;
      config.early_departure_margin = parseInt(data.early_departure_margin) || DEFAULT_CONFIG.early_departure_margin;
      config.frequency_tolerance = parseInt(data.frequency_tolerance) || DEFAULT_CONFIG.frequency_tolerance;
      config.ambiguous_margin = parseInt(data.ambiguous_margin) || DEFAULT_CONFIG.ambiguous_margin;

      alert('Configuration enregistrée avec succès.');
    }
  });
}

function exportTree() {
  if (!tree) {
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

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'anomaly_tree_config.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function importTree() {
  document.getElementById('importFile').click();
}

function validateTreeStructure(node) {
  // Vérifier si le noeud est valide
  if (!node) return false;

  // Vérifier si c'est une condition
  if (node.condition) {
    // Vérifier si branches existe et est un tableau
    if (!Array.isArray(node.branches)) {
      node.branches = [];
    }

    // Vérifier récursivement chaque branche
    let isValid = true;
    node.branches.forEach(branch => {
      // Vérifier si la branche a une valeur
      if (!branch.value) {
        branch.value = 'Valeur par défaut';
      }

      // Vérifier si la branche a des enfants
      if (branch.children) {
        isValid = isValid && validateTreeStructure(branch.children);
      }

      // Supprimer les branches au même niveau que children
      if (branch.children && branch.branches) {
        delete branch.branches;
      }
    });

    return isValid;
  }

  return true;
}

function handleImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const data = JSON.parse(e.target.result);

      // Vérifier si c'est un format ancien (juste l'arbre) ou nouveau (avec métadonnées)
      if (data.tree && data.config) {
        // Nouveau format
        if (validateTreeStructure(data.tree)) {
          tree = data.tree;
          config = { ...DEFAULT_CONFIG, ...data.config };
          alert(`Configuration importée avec succès (version ${data.version || 'inconnue'})`);
        } else {
          alert('Structure de l\'arbre invalide. Des corrections automatiques ont été appliquées.');
          tree = data.tree;
          config = { ...DEFAULT_CONFIG, ...data.config };
        }
      } else {
        // Ancien format (juste l'arbre)
        if (validateTreeStructure(data)) {
          tree = data;
          alert('Arbre importé avec succès (format ancien)');
        } else {
          alert('Structure de l\'arbre invalide. Des corrections automatiques ont été appliquées.');
          tree = data;
        }
      }

      renderTree();
    } catch (err) {
      alert('Erreur lors de l\'import : ' + err.message);
    }
  };
  reader.readAsText(file);
}

// Initial render
renderTree();