// ================================
// Scroll Restoration Configuration
// ================================
if ('scrollRestoration' in history) {
  history.scrollRestoration = 'manual';
}

// ===========================
// Remove URL Hash on Page Load
// ===========================
window.addEventListener('load', () => {
  if (window.location.hash) {
    history.replaceState(null, '', window.location.pathname + window.location.search);
  }
});

// =========================
// Highlight Row from URL Hash
// =========================
const highlightRowFromHash = () => {
  const hash = window.location.hash;
  if (hash && hash.startsWith('#log-')) {
    const logRow = document.querySelector(hash);
    if (logRow) {
      const tds = logRow.querySelectorAll('td');
      tds.forEach(td => td.classList.add('highlighted'));
      logRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => {
        tds.forEach(td => td.classList.remove('highlighted'));
      }, 5000);
    }
  }
};

window.addEventListener('load', highlightRowFromHash);
window.addEventListener('hashchange', highlightRowFromHash);

// =================
// jQuery DOM Ready
// =================
$(document).ready(function () {
  // Clone header row to add filter inputs
  $('#logsTable thead tr').clone(true).appendTo('#logsTable thead');

  // =============================
  // DataTables Column Configuration
  // =============================
  const COLUMNS_CONFIG = {
    noFilterColumns: [0, 8, 9],       // Index, Changes, Actions
    nonSortableColumns: [0, 8, 9],    // same columns not sortable
    defaultSortColumn: 6,              // Timestamp
    defaultSortDirection: 'desc',     // Descending order
    columnWidths: {
      0: '5%',
      1: '10%',
      2: '10%'
    }
  };

  // Add filter inputs to columns except excluded ones
  $('#logsTable thead tr:eq(1) th').each(function (colIndex) {
    if (COLUMNS_CONFIG.noFilterColumns.includes(colIndex)) {
      $(this).html('');
      return;
    }
    $(this).html('<input type="text" placeholder="Filter" style="width: 100%; font-size: 0.8rem;" />');

    $('input', this).on('keyup change clear', function () {
      const table = $('#logsTable').DataTable();
      if (table.column(colIndex).search() !== this.value) {
        table.column(colIndex).search(this.value).draw();
      }
    });
  });

  // Setup columnDefs for DataTables
  const columnDefs = [];
  if (COLUMNS_CONFIG.nonSortableColumns.length) {
    columnDefs.push({ targets: COLUMNS_CONFIG.nonSortableColumns, orderable: false });
  }
  Object.entries(COLUMNS_CONFIG.columnWidths).forEach(([idx, width]) => {
    columnDefs.push({ targets: [parseInt(idx)], width });
  });

  // ===========================
  // Initialize DataTable Plugin
  // ===========================
  const table = $('#logsTable').DataTable({
    orderCellsTop: true,
    fixedHeader: true,
    order: [[COLUMNS_CONFIG.defaultSortColumn, COLUMNS_CONFIG.defaultSortDirection]],
    pageLength: 25,
    lengthMenu: [[25, 50, 100, -1], [25, 50, 100, "All"]],
    columnDefs,
    language: {
      search: "",
      lengthMenu: "Show _MENU_ logs per page",
      zeroRecords: "No results found",
      info: "Page _PAGE_ of _PAGES_",
      infoEmpty: "No data available",
      infoFiltered: "(filtered from _MAX_ total logs)",
      paginate: { previous: "Previous", next: "Next" }
    },
    dom: 'lrtip',
    responsive: { details: { type: 'column', target: 'tr' } }
  });

  // =========================
  // Reapply Highlight on Draw
  // =========================
  table.on('draw', highlightRowFromHash);

  // ===================
  // Restore Button Click
  // ===================
  $(document).on('click', '.btn-restore', function (e) {
    e.preventDefault();
    const logIndex = parseInt($(this).data('log-index'));
    const logId = $(this).data('log-id');
    const logData = logsData[logIndex];

    if (!logData) {
      alert('Log data not found.');
      return;
    }

    let confirmMessage = `Do you want to restore changes from this log?\n\n`;
    confirmMessage += `User: ${logData.impacted_user_id || 'N/A'}\n`;
    confirmMessage += `Date: ${new Date(logData.timestamp).toLocaleString()}\n\n`;

    if (Object.keys(logData.changes).length > 0) {
      confirmMessage += `Changes to be restored:\n`;
      for (const [field, values] of Object.entries(logData.changes)) {
        if (field === 'profile_picture') {
          confirmMessage += `- ${field}: [Old picture will be restored]\n`;
        } else if (Array.isArray(values) && values.length >= 2) {
          const oldValue = values[0];
          const newValue = values[1];
          const displayOld = typeof oldValue === 'boolean' ? (oldValue ? 'Yes' : 'No') : oldValue;
          const displayNew = typeof newValue === 'boolean' ? (newValue ? 'Yes' : 'No') : newValue;
          confirmMessage += `- ${field}: "${displayNew}" → "${displayOld}"\n`;
        }
      }
    }

    if (confirm(confirmMessage)) {
      $('#restoreLogIndex').val(logIndex);
      $('#restoreForm').submit();
    }
  });
});