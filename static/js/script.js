    // Función para cambiar el rol en el formulario de registro
    function setRole(role) {
    const clientTab = document.getElementById('tab-client');
    const technicianTab = document.getElementById('tab-technician');
    const roleInput = document.getElementById('role-input');
    
    if (!clientTab || !technicianTab || !roleInput) return;
    
    roleInput.value = role;
    
    if (role === 'cliente') {
        clientTab.classList.add('bg-gradient-to-r', 'from-blue-500', 'to-cyan-500', 'text-white');
        clientTab.classList.remove('text-blue-200', 'hover:text-white');
        technicianTab.classList.remove('bg-gradient-to-r', 'from-blue-500', 'to-cyan-500', 'text-white');
        technicianTab.classList.add('text-blue-200', 'hover:text-white');
    } else {
        technicianTab.classList.add('bg-gradient-to-r', 'from-blue-500', 'to-cyan-500', 'text-white');
        technicianTab.classList.remove('text-blue-200', 'hover:text-white');
        clientTab.classList.remove('bg-gradient-to-r', 'from-blue-500', 'to-cyan-500', 'text-white');
        clientTab.classList.add('text-blue-200', 'hover:text-white');
    }
    }

    // Inicialización cuando el DOM está listo
    document.addEventListener('DOMContentLoaded', function() {
    console.log('JOSETEC - Sistema de Reparaciones cargado');

    // Inicializar select personalizado para Estado de la Orden
    document.querySelectorAll('[data-status-select]').forEach((container) => {
        const hiddenInput = container.querySelector('input[type="hidden"][name="status"]');
        const trigger = container.querySelector('.custom-select-trigger');
        const menu = container.querySelector('.custom-select-menu');
        const label = container.querySelector('.current-status');
        const options = container.querySelectorAll('.custom-select-option');

        if (!hiddenInput || !trigger || !menu || !label) return;

        const forceReflow = (el) => el.getBoundingClientRect();

        const openMenu = () => {
        if (!menu.classList.contains('hidden')) return;
        // Preparar para animación
        menu.classList.remove('hidden');
        menu.style.overflow = 'hidden';
        menu.style.maxHeight = '0px';
        trigger.setAttribute('aria-expanded', 'true');
        container.classList.add('open');
        forceReflow(menu);
        const target = Math.min(menu.scrollHeight, 240); // coincide con max-h-60 (~240px)
        menu.style.maxHeight = target + 'px';
        // Al terminar, permitir scroll
        const onEnd = (e) => {
            if (e.propertyName !== 'max-height') return;
            menu.style.overflow = 'auto';
            menu.removeEventListener('transitionend', onEnd);
        };
        menu.addEventListener('transitionend', onEnd);
        };

        const closeMenu = () => {
        if (menu.classList.contains('hidden')) return;
        // Animar hacia arriba
        menu.style.overflow = 'hidden';
        const current = menu.scrollHeight;
        menu.style.maxHeight = current + 'px';
        forceReflow(menu);
        menu.style.maxHeight = '0px';
        trigger.setAttribute('aria-expanded', 'false');
        const onEnd = (e) => {
            if (e.propertyName !== 'max-height') return;
            menu.classList.add('hidden');
            container.classList.remove('open');
            menu.removeEventListener('transitionend', onEnd);
        };
        menu.addEventListener('transitionend', onEnd);
        };
        const toggleMenu = (e) => {
        e.stopPropagation();
        if (menu.classList.contains('hidden')) openMenu(); else closeMenu();
        };

        const selectValue = (value, text, clickedOption) => {
        hiddenInput.value = value;
        label.textContent = text;
        options.forEach(o => {
            o.setAttribute('aria-selected', 'false');
            o.classList.remove('bg-white/15');
        });
        if (clickedOption) {
            clickedOption.setAttribute('aria-selected', 'true');
            clickedOption.classList.add('bg-white/15');
        }
        closeMenu();
        };

        trigger.addEventListener('click', toggleMenu);
        document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) closeMenu();
        });
        const getOptionsArray = () => Array.from(options);
        const getSelectedIndex = () => getOptionsArray().findIndex(o => o.getAttribute('aria-selected') === 'true');

        trigger.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { closeMenu(); return; }
        const opts = getOptionsArray();
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (menu.classList.contains('hidden')) { openMenu(); return; }
            let i = getSelectedIndex();
            i = Math.min(opts.length - 1, i + 1);
            opts[i].scrollIntoView({ block: 'nearest' });
            selectValue(opts[i].dataset.value, opts[i].textContent, opts[i]);
            openMenu();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (menu.classList.contains('hidden')) { openMenu(); return; }
            let i = getSelectedIndex();
            i = Math.max(0, i - 1);
            opts[i].scrollIntoView({ block: 'nearest' });
            selectValue(opts[i].dataset.value, opts[i].textContent, opts[i]);
            openMenu();
        } else if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (menu.classList.contains('hidden')) openMenu(); else closeMenu();
        }
        });
        options.forEach(opt => {
        opt.addEventListener('click', () => selectValue(opt.dataset.value, opt.textContent, opt));
        });
    });
    });
