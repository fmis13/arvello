'use strict';

const DatePicker = {
    init: function() {
        document.querySelectorAll('input[type="date"]').forEach(function(input) {
            if (input.type !== 'date') {
                const textInput = document.createElement('input');
                textInput.type = 'text';
                textInput.classList = input.classList;
                textInput.name = input.name;
                textInput.id = input.id;
                textInput.placeholder = 'DD.MM.YYYY';
                input.parentNode.replaceChild(textInput, input);
                textInput.addEventListener('blur', function() {
                    const value = this.value;
                    if (value) {
                        const pattern = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/;
                        const match = value.match(pattern);
                        if (match) {
                            const day = parseInt(match[1], 10);
                            const month = parseInt(match[2], 10) - 1;
                            const year = parseInt(match[3], 10);
                            const date = new Date(year, month, day);
                            if (date.getFullYear() === year && date.getMonth() === month && date.getDate() === day) {
                                this.classList.remove('is-invalid');
                                return;
                            }
                        }
                        this.classList.add('is-invalid');
                    }
                });
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', function() {
    DatePicker.init();
});
