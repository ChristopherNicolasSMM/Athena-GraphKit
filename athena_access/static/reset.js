const field = document.querySelector('#resetToken');
if (field && location.hash.length > 1) {
  field.value = location.hash.slice(1);
  history.replaceState(null, '', location.pathname);
}
