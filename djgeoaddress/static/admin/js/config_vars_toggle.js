/**
 * Gestion de l'affichage/masquage des valeurs de variables de configuration
 */
(function() {
    'use strict';
    
    function initConfigVarsToggle($) {
        console.log('Config vars toggle initialized');
        
        // Attacher l'événement click sur toutes les icônes d'œil
        $(document).on('click', '.config-eye', function(e) {
            console.log('Eye clicked!');
            e.preventDefault();
            e.stopPropagation();
            
            var $eye = $(this);
            var varName = $eye.data('var');
            console.log('Variable name:', varName);
            
            var $masked = $('.config-value-masked[data-var="' + varName + '"]');
            var $revealed = $('.config-value-revealed[data-var="' + varName + '"]');
            
            console.log('Masked elements found:', $masked.length);
            console.log('Revealed elements found:', $revealed.length);
            console.log('Revealed visible:', $revealed.is(':visible'));
            
            if ($revealed.is(':visible')) {
                // Masquer la valeur
                console.log('Hiding value');
                $revealed.hide();
                $masked.show();
                $eye.attr('title', 'Cliquer pour afficher');
            } else {
                // Afficher la valeur
                console.log('Showing value');
                $masked.hide();
                $revealed.show();
                $eye.attr('title', 'Cliquer pour masquer');
            }
        });
    }
    
    // Attendre que django.jQuery soit disponible
    function waitForJQuery() {
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
            initConfigVarsToggle(django.jQuery);
        } else {
            setTimeout(waitForJQuery, 50);
        }
    }
    
    // Démarrer l'attente
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForJQuery);
    } else {
        waitForJQuery();
    }
})();
