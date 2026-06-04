(function () {
  document.querySelectorAll('.emailAuto, #emailAuto').forEach((emailInput) => {
    emailInput.addEventListener('blur', () => {
      const value = emailInput.value.trim();
      if (value && !value.includes('@')) {
        emailInput.value = value + '@validade.app';
      }
    });
  });

  const codigo = document.getElementById('codigoProduto');
  const nome = document.getElementById('nomeProduto');
  if (codigo && nome) {
    let timer = null;
    let controller = null;
    const CACHE_KEY = 'valicontrol_lookup_cache_v2';

    function loadCache() {
      try { return JSON.parse(sessionStorage.getItem(CACHE_KEY) || '{}'); }
      catch (error) { return {}; }
    }

    function saveCache(cache) {
      try {
        const entries = Object.entries(cache).slice(-250);
        sessionStorage.setItem(CACHE_KEY, JSON.stringify(Object.fromEntries(entries)));
      } catch (error) {}
    }

    function setNomeFromCache(item) {
      if (item && item.nome && !nome.dataset.userEdited) {
        nome.value = item.nome;
        nome.dataset.autoFilled = '1';
      }
    }

    async function consultarCodigo(imediato) {
      const value = codigo.value.trim();
      if (!value || value.length < 3) return;

      const cache = loadCache();
      if (cache[value]) {
        setNomeFromCache(cache[value]);
        return;
      }

      if (controller) controller.abort();
      controller = new AbortController();

      const oldPlaceholder = nome.placeholder;
      if (!nome.dataset.userEdited && value.length >= 6) {
        nome.placeholder = 'Consultando código...';
      }

      try {
        const response = await fetch(`/api/produto-lookup/?codigo=${encodeURIComponent(value)}`, {
          signal: controller.signal,
          cache: 'force-cache',
          headers: { 'Accept': 'application/json' }
        });
        const data = await response.json();
        if (data.found && data.nome) {
          cache[value] = data;
          saveCache(cache);
          setNomeFromCache(data);
        }
      } catch (error) {
        if (error.name !== 'AbortError') console.warn('Lookup indisponível', error);
      } finally {
        if (nome.placeholder === 'Consultando código...') nome.placeholder = oldPlaceholder || 'Nome do produto';
      }
    }

    codigo.addEventListener('input', () => {
      clearTimeout(timer);
      const value = codigo.value.trim();
      if (!value || value.length < 3) return;
      // Local era instantâneo, mas na internet cada tecla gera rede. O debounce evita
      // várias requisições ao mesmo tempo e deixa a tela mais estável.
      const delay = value.length >= 8 ? 260 : 430;
      timer = setTimeout(() => consultarCodigo(false), delay);
    });

    codigo.addEventListener('paste', () => {
      clearTimeout(timer);
      timer = setTimeout(() => consultarCodigo(true), 80);
    });

    codigo.addEventListener('blur', () => {
      clearTimeout(timer);
      consultarCodigo(true);
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
