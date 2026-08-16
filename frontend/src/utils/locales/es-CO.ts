/**
 * es-CO PrimeVue locale (task S0-T3, design D5, spec BEH-7).
 *
 * Authored plain object — PrimeVue ships no es locale, and the key surface
 * (paginator/datepicker/filter/aria) differs from Element Plus's `el.*`
 * shape. Values mirror the Spanish labels users see today with
 * `app.use(ElementPlus, { locale: es })`:
 *   - EP pagination `Ir a` / `Total {total}` -> paginator aria + Paginator
 *     `currentPageReportTemplate: 'Total {totalRecords}'` (set per usage)
 *   - EP datepicker months/weeks -> monthNames/dayNames
 *   - EP select/table messages -> empty* / filter keys
 */
import type { PrimeVueLocaleOptions } from '@primevue/core/config'

const esCO: PrimeVueLocaleOptions = {
  // Filter operators (EP table filters: "Contiene", "Empieza con"...).
  startsWith: 'Empieza con',
  contains: 'Contiene',
  notContains: 'No contiene',
  endsWith: 'Termina con',
  equals: 'Igual a',
  notEquals: 'No igual a',
  noFilter: 'Sin filtro',
  lt: 'Menor que',
  lte: 'Menor o igual que',
  gt: 'Mayor que',
  gte: 'Mayor o igual que',
  dateIs: 'La fecha es',
  dateIsNot: 'La fecha no es',
  dateBefore: 'La fecha es anterior a',
  dateAfter: 'La fecha es posterior a',
  clear: 'Limpiar',
  apply: 'Aplicar',
  matchAll: 'Coincidir todo',
  matchAny: 'Coincidir cualquiera',
  addRule: 'Agregar regla',
  removeRule: 'Quitar regla',

  // EP messagebox confirm/cancel -> accept/reject; upload labels.
  accept: 'Aceptar',
  reject: 'Cancelar',
  choose: 'Seleccionar',
  upload: 'Subir',
  cancel: 'Cancelar',
  completed: 'Completado',
  pending: 'Pendiente',
  fileSizeTypes: ['B', 'KB', 'MB', 'GB', 'TB'],

  // DatePicker (EP es months/weeks; lowercase Colombian convention).
  dayNames: ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'],
  dayNamesShort: ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'],
  dayNamesMin: ['D', 'L', 'M', 'X', 'J', 'V', 'S'],
  monthNames: [
    'enero',
    'febrero',
    'marzo',
    'abril',
    'mayo',
    'junio',
    'julio',
    'agosto',
    'septiembre',
    'octubre',
    'noviembre',
    'diciembre',
  ],
  monthNamesShort: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
  chooseYear: 'Elegir año',
  chooseMonth: 'Elegir mes',
  chooseDate: 'Elegir fecha',
  prevDecade: 'Década anterior',
  nextDecade: 'Década siguiente',
  prevYear: 'Año anterior',
  nextYear: 'Año siguiente',
  prevMonth: 'Mes anterior',
  nextMonth: 'Mes siguiente',
  prevHour: 'Hora anterior',
  nextHour: 'Hora siguiente',
  prevMinute: 'Minuto anterior',
  nextMinute: 'Minuto siguiente',
  prevSecond: 'Segundo anterior',
  nextSecond: 'Segundo siguiente',
  am: 'a. m.',
  pm: 'p. m.',
  today: 'Hoy',
  weekHeader: 'Semana',
  firstDayOfWeek: 0, // Matches EP es default (Sunday first) — D5.
  dateFormat: 'dd/mm/yy',

  // Empty-state / search messages (EP "Sin datos", "No hay datos que coincidan").
  emptyFilterMessage: 'No hay datos que coincidan',
  searchMessage: 'Buscar',
  selectionMessage: 'seleccionados',
  emptySelectionMessage: 'Nada seleccionado',
  emptySearchMessage: 'No se encontraron resultados',
  emptyMessage: 'Sin datos',

  aria: {
    trueLabel: 'Verdadero',
    falseLabel: 'Falso',
    nullLabel: 'No seleccionado',
    star: 'estrella',
    stars: 'estrellas',
    selectAll: 'Seleccionar todos',
    unselectAll: 'Quitar selección',
    close: 'Cerrar',
    previous: 'Anterior',
    next: 'Siguiente',
    navigation: 'Navegación',
    scrollTop: 'Desplazarse arriba',
    moveUp: 'Mover arriba',
    moveTop: 'Mover al inicio',
    moveDown: 'Mover abajo',
    moveBottom: 'Mover al final',
    moveToTarget: 'Mover al destino',
    moveToSource: 'Mover al origen',
    moveAllToTarget: 'Mover todo al destino',
    moveAllToSource: 'Mover todo al origen',

    // Paginator aria (EP pagination `Ir a` / rows per page).
    pageLabel: 'Página',
    firstPageLabel: 'Primera página',
    lastPageLabel: 'Última página',
    nextPageLabel: 'Página siguiente',
    prevPageLabel: 'Página anterior',
    rowsPerPageLabel: 'Filas por página',
    jumpToPageDropdownLabel: 'Ir a la página',
    jumpToPageInputLabel: 'Ir a',

    // Table row aria.
    selectRow: 'Seleccionar fila',
    unselectRow: 'Quitar selección de fila',
    expandRow: 'Expandir fila',
    collapseRow: 'Contraer fila',
    showFilterMenu: 'Mostrar menú de filtros',
    hideFilterMenu: 'Ocultar menú de filtros',
    filterOperator: 'Operador de filtro',
    filterConstraint: 'Restricción de filtro',
    editRow: 'Editar fila',
    saveEdit: 'Guardar edición',
    cancelEdit: 'Cancelar edición',
    listView: 'Vista de lista',
    gridView: 'Vista de cuadrícula',
    slide: 'Diapositiva',
    slideNumber: 'Diapositiva',
    zoomImage: 'Ampliar imagen',
    zoomIn: 'Acercar',
    zoomOut: 'Alejar',
    rotateRight: 'Rotar a la derecha',
    rotateLeft: 'Rotar a la izquierda',
    listLabel: 'Lista',
  },
}

export default esCO