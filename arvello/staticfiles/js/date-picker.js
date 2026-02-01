'use strict';

const DatePicker = {
    parseShorthand: function(value) {
        // Parse shorthand formats like "1,6,26" or "1.6.26" or "1/6/26"
        const pattern = /^(\d{1,2})[.,\/](\d{1,2})[.,\/](\d{2,4})$/;
        const match = value.match(pattern);
        if (match) {
            const day = parseInt(match[1], 10);
            const month = parseInt(match[2], 10) - 1;
            let year = parseInt(match[3], 10);
            
            // Convert 2-digit year to 4-digit (assumes 20xx for values < 50, 19xx otherwise)
            if (year < 100) {
                year = year < 50 ? 2000 + year : 1900 + year;
            }
            
            const date = new Date(year, month, day);
            if (date.getFullYear() === year && date.getMonth() === month && date.getDate() === day) {
                return date;
            }
        }
        return null;
    },

    parseCroatian: function(value) {
        // Parse full Croatian format "dd.mm.yyyy" or "d.m.yyyy"
        const pattern = /^(\d{1,2})\.(\d{1,2})\.(\d{4})\.?$/;
        const match = value.match(pattern);
        if (match) {
            const day = parseInt(match[1], 10);
            const month = parseInt(match[2], 10) - 1;
            const year = parseInt(match[3], 10);
            const date = new Date(year, month, day);
            if (date.getFullYear() === year && date.getMonth() === month && date.getDate() === day) {
                return date;
            }
        }
        return null;
    },

    formatCroatian: function(date) {
        if (!date) return '';
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}.`;
    },

    formatISO: function(date) {
        if (!date) return '';
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        return `${year}-${month}-${day}`;
    },

    init: function() {
        const self = this;
        
        document.querySelectorAll('input[type="date"]').forEach(function(dateInput) {
            // Skip if already initialized
            if (dateInput.dataset.croDateInit) return;
            dateInput.dataset.croDateInit = 'true';
            
            const originalName = dateInput.name;
            const originalId = dateInput.id;
            const originalValue = dateInput.value;
            const originalClass = dateInput.className;
            
            // Create wrapper using input-group for proper Bootstrap styling
            const wrapper = document.createElement('div');
            wrapper.className = 'input-group';
            dateInput.parentNode.insertBefore(wrapper, dateInput);
            
            // Create visible text input for Croatian format (display only, no name)
            const textInput = document.createElement('input');
            textInput.type = 'text';
            textInput.className = originalClass;
            textInput.placeholder = 'dd.mm.gggg';
            textInput.id = originalId + '_display';
            textInput.autocomplete = 'off';
            
            // Create hidden input for form submission (ISO format)
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = originalName;
            hiddenInput.id = originalId;
            
            // Create calendar button
            const calendarBtn = document.createElement('button');
            calendarBtn.type = 'button';
            calendarBtn.className = 'btn btn-outline-secondary';
            calendarBtn.innerHTML = '<i class="bi bi-calendar3"></i>';
            calendarBtn.title = 'Odaberi datum';
            
            // Convert original date input to picker only (no form submission)
            dateInput.type = 'date';
            dateInput.name = '';  // Remove name so it doesn't submit
            dateInput.id = originalId + '_picker';
            dateInput.className = 'visually-hidden position-absolute';
            dateInput.style.opacity = '0';
            dateInput.style.pointerEvents = 'none';
            dateInput.tabIndex = -1;
            
            // Convert initial value to Croatian format
            if (originalValue) {
                const initialDate = new Date(originalValue + 'T00:00:00');
                if (!isNaN(initialDate)) {
                    textInput.value = self.formatCroatian(initialDate);
                    hiddenInput.value = originalValue;
                }
            }
            
            wrapper.appendChild(textInput);
            wrapper.appendChild(calendarBtn);
            wrapper.appendChild(hiddenInput);
            wrapper.appendChild(dateInput);
            
            // Handle text input - parse on blur and also on Enter
            function parseAndUpdate() {
                const value = textInput.value.trim();
                if (!value) {
                    dateInput.value = '';
                    hiddenInput.value = '';
                    textInput.classList.remove('is-invalid');
                    return true;
                }
                
                // Try shorthand first, then full Croatian format
                let date = self.parseShorthand(value) || self.parseCroatian(value);
                
                if (date) {
                    const isoValue = self.formatISO(date);
                    dateInput.value = isoValue;
                    hiddenInput.value = isoValue;
                    textInput.value = self.formatCroatian(date);
                    textInput.classList.remove('is-invalid');
                    return true;
                } else {
                    textInput.classList.add('is-invalid');
                    return false;
                }
            }
            
            textInput.addEventListener('blur', parseAndUpdate);
            
            textInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    parseAndUpdate();
                }
            });
            
            // Calendar button opens the native date picker
            calendarBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                // Try showPicker first (modern browsers), fallback to click
                if (typeof dateInput.showPicker === 'function') {
                    try {
                        dateInput.showPicker();
                    } catch (err) {
                        dateInput.click();
                    }
                } else {
                    dateInput.click();
                }
            });
            
            // Handle calendar picker change
            dateInput.addEventListener('change', function() {
                if (this.value) {
                    const date = new Date(this.value + 'T00:00:00');
                    if (!isNaN(date)) {
                        textInput.value = self.formatCroatian(date);
                        hiddenInput.value = this.value;
                        textInput.classList.remove('is-invalid');
                    }
                } else {
                    textInput.value = '';
                    hiddenInput.value = '';
                }
            });
        });
    }
};

document.addEventListener('DOMContentLoaded', function() {
    DatePicker.init();
});
