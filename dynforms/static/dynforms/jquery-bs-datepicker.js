(function($) {
        $.fn.datePicker = function(options) {
            // Default settings
            const settings = $.extend({
                dateFormat: 'YYYY-MM-DD',
                initialDate: new Date(), // Date object or string parsable by new Date()
                multiple: false // Currently only single date selection is supported
            }, options);

            const leftArrow = '<svg  xmlns="http://www.w3.org/2000/svg"  width="1em"  height="1em"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="3"  stroke-linecap="round"  stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M15 6l-6 6l6 6" /></svg>';
            const rightArrow = '<svg  xmlns="http://www.w3.org/2000/svg"  width="1em"  height="1em"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="3"  stroke-linecap="round"  stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M9 6l6 6l-6 6" /></svg>';

            // Helper function to format date
            function formatDate(date, formatStr) {
                const d = new Date(date);
                const year = d.getUTCFullYear();
                const month = ('0' + (d.getUTCMonth() + 1)).slice(-2);
                const day = ('0' + d.getUTCDate()).slice(-2);
                return formatStr.replace('YYYY', year).replace('MM', month).replace('DD', day);
            }

            // Helper function to parse date from string
            function parseDates(dateStr) {
                const parts = dateStr.trim().split(/\s*,\s+/);
                let dates = [];
                for (const part of parts) {
                    try {
                        let d = new Date(part);
                        if (!isNaN(d.getTime())) {
                            dates.push(d);
                        }
                    } catch(err) {
                        console.error('Invalid date format:', part, 'Error:', err);
                    }
                }
                return dates;
            }

            // Generates the HTML for the popover title (navigation)
            function generatePopoverTitle($input) {
                const state = $input.data('datepickerState');
                let titleText = '';
                let titleDataAction = 'title';

                if (state.currentView === 'days') {
                    titleText = state.currentDate.toLocaleString('default', { month: 'long' }) + ' ' + state.currentDate.getUTCFullYear();
                } else if (state.currentView === 'months') {
                    titleText = state.currentDate.getUTCFullYear().toString();
                } else if (state.currentView === 'years') {
                    const currentYear = state.currentDate.getUTCFullYear();
                    const startYear = Math.floor(currentYear / 20) * 20;
                    titleText = `${startYear} - ${startYear + 19}`;
                    titleDataAction = 'noop'; // No further drill-up from years view title
                }
                return `<button type="button" class="btn btn-link btn-sm px-2 py-1 dp-action" data-action="prev" aria-label="Previous">${leftArrow}</button>
                        <span class="dp-nav-title dp-action" data-action="${titleDataAction}">${titleText}</span>
                        <button type="button" class="btn btn-link btn-sm px-2 py-1 dp-action" data-action="next" aria-label="Next">${rightArrow}</button>`;
            }

            // Generates the HTML for the calendar grid (days, months, or years)
            function generateCalendarGrid($input) {
                const state = $input.data('datepickerState');
                const today = new Date();
                today.setHours(0, 0, 0, 0); // Normalize today for comparison

                let html = '<table class="table table-sm dp-table">';

                if (state.currentView === 'days') {
                    html += '<thead><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr></thead>';
                    html += '<tbody>';
                    const year = state.currentDate.getUTCFullYear();
                    const month = state.currentDate.getUTCMonth();
                    const firstDayOfMonth = new Date(year, month, 1);
                    const lastDayOfMonth = new Date(year, month + 1, 0);
                    const numDays = lastDayOfMonth.getUTCDate();
                    let startDayOfWeek = firstDayOfMonth.getDay(); // 0 (Sun) - 6 (Sat)

                    let date = 1;
                    for (let i = 0; i < 6; i++) { // Max 6 rows for a month
                        html += '<tr>';
                        for (let j = 0; j < 7; j++) {
                            if (i === 0 && j < startDayOfWeek) {
                                html += '<td class="dp-empty"></td>'; // Empty cell for days before start of month
                            } else if (date > numDays) {
                                html += '<td class="dp-empty"></td>'; // Empty cell for days after end of month
                            } else {
                                const cellDate = new Date(year, month, date);
                                cellDate.setHours(0,0,0,0);
                                let classes = 'dp-action';
                                if (cellDate.getTime() === today.getTime()) classes += ' table-info'; // Today
                                for (const selectedDate of state.selectedDates) {
                                    if (selectedDate.getTime() === cellDate.getTime()) {
                                        classes += ' table-primary'; // Selected
                                        break; // No need to check further if already selected
                                    }
                                }
                                html += `<td class="${classes}" data-action="select-day" data-day="${date}">${date}</td>`;
                                date++;
                            }
                        }
                        html += '</tr>';
                        if (date > numDays) {
                            break;
                        }
                    }
                    html += '</tbody>';
                } else if (state.currentView === 'months') {
                    html += '<tbody>';
                    const months = state.currentDate.toLocaleDateString('default', { year: 'numeric' }) // just to have an array of 12
                        .split(' ') // this is a hack, better to have a fixed array or use Intl more reliably
                        .map((_, i) => new Date(2000, i).toLocaleString('default', { month: 'short' }));
                        // A more robust way for month names:
                    const monthNames = Array.from({length: 12}, (e, i) => {
                        return new Date(null, i + 1, null).toLocaleDateString('en', {month: 'short'});
                    });

                    let monthIdx = 0;
                    for (let i = 0; i < 3; i++) { // 3 rows
                        html += '<tr>';
                        for (let j = 0; j < 4; j++) { // 4 months per row
                            if (monthIdx < 12) {
                                html += `<td class="dp-action" data-action="select-month" data-month="${monthIdx}">${monthNames[monthIdx]}</td>`;
                                monthIdx++;
                            } else {
                                html += '<td class="dp-empty"></td>';
                            }
                        }
                        html += '</tr>';
                    }
                    html += '</tbody>';
                } else if (state.currentView === 'years') {
                    html += '<tbody>';
                    const currentYearInView = state.currentDate.getUTCFullYear();
                    let yearVal = Math.floor(currentYearInView / 20) * 20;
                    for (let i = 0; i < 5; i++) { // 5 rows
                        html += '<tr>';
                        for (let j = 0; j < 4; j++) { // 4 years per row
                            html += `<td class="dp-action" data-action="select-year" data-year="${yearVal}">${yearVal}</td>`;
                            yearVal++;
                        }
                        html += '</tr>';
                    }
                    html += '</tbody>';
                }
                html += '</table>';
                return html;
            }

            // Updates the input field value
            function updateInputValue($input) {
                const state = $input.data('datepickerState');
                let formattedDates = [];
                for (const selectedDate of state.selectedDates) {
                    formattedDates.push(formatDate(selectedDate, state.settings.dateFormat));
                }
                const formatted = formattedDates.join(', '); // Join multiple dates if needed
                $input.val(formatted);
                $input.change(); // Trigger change event to notify any listeners
                if (state.settings.multiple) {
                    $input.attr('data-selected-dates', JSON.stringify(state.selectedDates.map(d => d.toISOString())));
                } else if (state.selectedDates.length > 0) {
                    $input.trigger('changeDate', state.selectedDates[0]); // Trigger change event for any listeners
                } else {
                    $input.trigger('changeDate', null); // Trigger change event for any listeners
                }
            }

            // Handles clicks on actions within the popover
            function handlePopoverAction($input, $target) {
                let state = $input.data('datepickerState');
                state.selectedDates = parseDates($input.val());
                const action = $target.data('action');

                if (action === 'prev') {
                    if (state.currentView === 'days') state.currentDate.setMonth(state.currentDate.getUTCMonth() - 1);
                    else if (state.currentView === 'months') state.currentDate.setFullYear(state.currentDate.getUTCFullYear() - 1);
                    else if (state.currentView === 'years') state.currentDate.setFullYear(state.currentDate.getUTCFullYear() - 20);
                } else if (action === 'next') {
                    if (state.currentView === 'days') state.currentDate.setMonth(state.currentDate.getUTCMonth() + 1);
                    else if (state.currentView === 'months') state.currentDate.setFullYear(state.currentDate.getUTCFullYear() + 1);
                    else if (state.currentView === 'years') state.currentDate.setFullYear(state.currentDate.getUTCFullYear() + 20);
                } else if (action === 'title') {
                    if (state.currentView === 'days') state.currentView = 'months';
                    else if (state.currentView === 'months') state.currentView = 'years';
                    // No action if already in years view or titleDataAction was 'noop'
                } else if (action === 'select-day') {
                    const day = parseInt($target.data('day'));
                    // Ensure month and year are from currentDate to avoid issues if it changed
                    const selectedDate = new Date(state.currentDate.getUTCFullYear(), state.currentDate.getUTCMonth(), day);
                    if (state.settings.multiple) {
                        state.selectedDates.push(selectedDate); // Add to selection
                    } else {
                        state.selectedDates = [selectedDate]; // Single select
                    }
                    updateInputValue($input);
                    bootstrap.Popover.getInstance($input[0]).hide();
                    return; // Exit early as popover is hidden
                } else if (action === 'select-month') {
                    const month = parseInt($target.data('month'));
                    state.currentDate.setMonth(month);
                    state.currentView = 'days';
                } else if (action === 'select-year') {
                    const year = parseInt($target.data('year'));
                    state.currentDate.setFullYear(year);
                    state.currentDate.setMonth(0); // Default to Jan when selecting a year
                    state.currentView = 'months';
                } else if (action === 'noop') {
                    return; // Do nothing for actions marked as noop
                }


                $input.data('datepickerState', state); // Save updated state

                // Manually trigger popover content update
                const popoverInstance = bootstrap.Popover.getInstance($input[0]);
                if (popoverInstance) {
                    // This forces Bootstrap to re-render title and content using the functions
                     popoverInstance.setContent({
                        '.popover-header': generatePopoverTitle($input),
                        '.popover-body': generateCalendarGrid($input)
                    });
                }
            }

            // Initialize for each element in the jQuery selection
            return this.each(function() {
                const $input = $(this);
                // Try to parse the initial date from input value if it's set and valid, otherwise use settings.initialDate

                let inputDateStrings = $input.val().trim().split(/\s*,\s+/);
                let initialDates = parseDates($input.val());
                let initialDateFromInput;

                if (inputDateStrings.length > 0 && inputDateStrings[0]) {
                    initialDateFromInput = new Date(inputDateStrings[0]);
                }
                let initialPickerDate = settings.initialDate;

                if (initialDateFromInput && !isNaN(initialDateFromInput.getTime())) {
                    // If input has a valid date, use it for the picker's initial month/year view
                    // And also for the initial selection if desired (currently, selection happens on click)
                    initialPickerDate = initialDateFromInput;
                } else if (typeof settings.initialDate === 'string') {
                     initialPickerDate = new Date(settings.initialDate);
                     if(isNaN(initialPickerDate.getTime())) initialPickerDate = new Date(); // Fallback if string is invalid
                } else if (!(settings.initialDate instanceof Date)) {
                     initialPickerDate = new Date(); // Fallback if not a Date object
                }

                const state = {
                    currentDate: new Date(initialPickerDate.getUTCFullYear(), initialPickerDate.getUTCMonth(), 1), // Start view at 1st of month
                    selectedDates: initialDates, // Initialize with date from input if valid
                    currentView: 'days', // 'days', 'months', 'years'
                    settings: settings,
                    inputElement: $input[0]
                };
                $input.data('datepickerState', state);

                // Initialize popover
                const popover = new bootstrap.Popover($input[0], {
                    html: true,
                    sanitize: false, // We are generating trusted HTML
                    title: () => generatePopoverTitle($input),
                    content: () => generateCalendarGrid($input),
                    placement: 'bottom',
                    trigger: 'click', // Bootstrap handles show/hide on click
                    customClass: 'datepicker-popover rounded-md shadow-lg' // Add a custom class for styling
                });

                // Event listener for when popover is shown
                // This is where we attach event handlers to the popover content
                $input.on('shown.bs.popover', function () {
                    const popoverTip = document.getElementById($input.attr('aria-describedby'));
                    if (popoverTip) {
                        // Detach previous handlers to avoid multiple bindings
                        $(popoverTip).off('.datepicker').on('click.datepicker', '.dp-action', function(e) {
                            e.stopPropagation(); // Prevent click from bubbling to document and closing popover immediately
                            handlePopoverAction($input, $(this));
                        });
                    }
                });

                // Close popover if a user clicks outside of it.
                $(document).on('click', function(e) {
                    const popoverTip = document.getElementById($input.attr('aria-describedby'));
                    if (popoverTip && !$(popoverTip).is(e.target) && !$.contains(popoverTip, e.target) && !$(e.target).is($input)) {
                        popover.hide();
                    }
                });
            });
        };
    })(jQuery);