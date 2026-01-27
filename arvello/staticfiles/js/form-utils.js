'use strict';

const FormUtils = {
    updateElementIndex: function(el, prefix, newIndex) {
        const idRegex = new RegExp('(' + prefix + '-(\\d+))');
        const replacement = prefix + '-' + newIndex;
        
        if (el.getAttribute('for')) {
            el.setAttribute('for', el.getAttribute('for').replace(idRegex, replacement));
        }
        if (el.id) {
            el.id = el.id.replace(idRegex, replacement);
        }
        if (el.name) {
            el.name = el.name.replace(idRegex, replacement);
        }
    },
    
    cloneMore: function(selector, prefix) {
        const container = document.querySelector(selector);
        const newElement = container.cloneNode(true);
        const totalForms = document.getElementById('id_' + prefix + '-TOTAL_FORMS');
        let total = parseInt(totalForms.value, 10);
        
        newElement.querySelectorAll('input, select, textarea').forEach(function(input) {
            if (input.type !== 'button' && input.type !== 'submit' && input.type !== 'reset') {
                if (input.name) {
                    const name = input.name.replace('-' + (total - 1) + '-', '-' + total + '-');
                    const id = 'id_' + name;
                    input.name = name;
                    input.id = id;
                    input.value = '';
                    
                    if (input.type === 'checkbox') {
                        input.checked = false;
                    }
                }
            }
        });
        
        newElement.querySelectorAll('label').forEach(function(label) {
            const forValue = label.getAttribute('for');
            if (forValue) {
                label.setAttribute('for', forValue.replace('-' + (total - 1) + '-', '-' + total + '-'));
            }
        });
        
        total++;
        totalForms.value = total;
        
        container.parentNode.insertBefore(newElement, null);
        
        const buttons = document.querySelectorAll('.buttonDynamic');
        for (let i = 1; i < buttons.length; i++) {
            buttons[i].style.display = 'none';
        }
        
        return false;
    }
};

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        if (e.target.matches('.buttonDynamic')) {
            e.preventDefault();
            
            const isOfferForm = window.location.pathname.includes('offer');
            const prefix = isOfferForm ? 'offerproduct_set' : 'invoiceproduct_set';
            
            FormUtils.cloneMore('.formsetDynamic:last', prefix);
        }
    });
});
