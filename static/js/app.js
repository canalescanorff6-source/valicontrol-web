(function () {
  const emailInput = document.getElementById('emailAuto');
  if (emailInput) {
    emailInput.addEventListener('blur', () => {
      const value = emailInput.value.trim();
      if (value && !value.includes('@')) {
        emailInput.value = value + '@app.com';
      }
    });
  }

  const codigo = document.getElementById('codigoProduto');
  const nome = document.getElementById('nomeProduto');
  if (codigo && nome) {
    let timer = null;
    codigo.addEventListener('input', () => {
      clearTimeout(timer);
      const value = codigo.value.trim();
      if (!value || value.length < 3) return;
      timer = setTimeout(async () => {
        try {
          const response = await fetch(`/api/produto-lookup/?codigo=${encodeURIComponent(value)}`);
          const data = await response.json();
          if (data.found && data.nome && !nome.dataset.userEdited) {
            nome.value = data.nome;
          }
        } catch (error) {
          console.warn('Lookup indisponível', error);
        }
      }, 280);
    });
    nome.addEventListener('input', () => {
      nome.dataset.userEdited = '1';
    });
  }

  document.querySelectorAll('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const target = document.querySelector(btn.dataset.copy);
      if (!target) return;
      try {
        await navigator.clipboard.writeText(target.value || target.textContent || '');
        const original = btn.textContent;
        btn.textContent = 'Copiado!';
        setTimeout(() => { btn.textContent = original; }, 1600);
      } catch (error) {
        target.select && target.select();
      }
    });
  });

  setTimeout(() => {
    document.querySelectorAll('.message').forEach((item) => {
      item.style.opacity = '0';
      item.style.transform = 'translateY(-6px)';
      item.style.transition = 'opacity .25s, transform .25s';
      setTimeout(() => item.remove(), 300);
    });
  }, 5000);
})();
