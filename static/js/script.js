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
});
