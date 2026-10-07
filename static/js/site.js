const toggle = document.querySelector(".nav-toggle");
const nav = document.querySelector("#primary-nav");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!expanded));
    nav.classList.toggle("open");
  });
}

document.querySelectorAll('.primary-nav a').forEach(link => {
  if (link.getAttribute('href') === window.location.pathname || (link.getAttribute('href') === '/news/' && /^\/(news|events)\//.test(window.location.pathname))) link.setAttribute('aria-current', 'page');
});
document.querySelectorAll('.news-filters input[type="radio"]').forEach(input => input.addEventListener('change', () => input.form.requestSubmit()));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && nav?.classList.contains('open')) {
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  }
});
const searchDialog = document.querySelector('#site-search');
document.querySelector('[data-open-search]')?.addEventListener('click', () => {
  searchDialog.showModal();
  document.querySelector('#global-query').focus();
});
document.querySelector('[data-close-search]')?.addEventListener('click', () => searchDialog.close());
searchDialog?.addEventListener('click', event => {
  if (event.target !== searchDialog) return;
  const bounds = searchDialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) searchDialog.close();
});
const topButton = document.querySelector('.back-top');
window.addEventListener('scroll', () => { topButton.hidden = window.scrollY < 600; }, { passive: true });
topButton?.addEventListener('click', () => window.scrollTo({ top: 0 }));

const audienceTabs = [...document.querySelectorAll('[data-audience]')];
function selectAudience(tab) {
  audienceTabs.forEach(item => {
    const selected = item === tab;
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
    document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
  });
}
audienceTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectAudience(tab));
  tab.addEventListener('keydown', event => {
    let target;
    if (event.key === 'ArrowRight') target = audienceTabs[(index + 1) % audienceTabs.length];
    if (event.key === 'ArrowLeft') target = audienceTabs[(index + audienceTabs.length - 1) % audienceTabs.length];
    if (event.key === 'Home') target = audienceTabs[0];
    if (event.key === 'End') target = audienceTabs.at(-1);
    if (target) { event.preventDefault(); selectAudience(target); target.focus(); }
  });
});

const serviceFilter = document.querySelector('#service-filter');
const departmentFilter = document.querySelector('.departments-section .department-filters');
if (departmentFilter) {
  const search = departmentFilter.querySelector('input[type="search"]');
  const rows = [...document.querySelectorAll('.department-row')];
  const filterDepartments = () => {
    const branch = departmentFilter.querySelector('input[name="branch"]:checked').value;
    const query = search.value.trim().toLowerCase();
    let count = 0;
    rows.forEach(row => {
      row.hidden = (branch !== 'all' && row.dataset.branch !== branch) || !row.dataset.search.includes(query);
      if (!row.hidden) count++;
    });
    document.querySelector('#department-count').textContent = `${count} office${count === 1 ? '' : 's'}`;
    document.querySelector('#department-empty').hidden = count !== 0;
  };
  departmentFilter.addEventListener('submit', event => { event.preventDefault(); filterDepartments(); });
  search.addEventListener('input', filterDepartments);
  departmentFilter.querySelectorAll('input[name="branch"]').forEach(input => input.addEventListener('change', filterDepartments));
  filterDepartments();
}
serviceFilter?.addEventListener('input', () => {
  const query = serviceFilter.value.trim().toLowerCase();
  let count = 0;
  document.querySelectorAll('.service-directory-item').forEach(item => {
    item.hidden = !item.dataset.search.includes(query);
    if (!item.hidden) count++;
  });
  document.querySelector('#service-count').textContent = `${count} service${count === 1 ? '' : 's'}`;
  document.querySelector('#service-empty').hidden = count !== 0;
});
const serviceData = document.querySelector('#service-data');
if (serviceData) {
  const services = JSON.parse(serviceData.textContent);
  const serviceSelect = document.querySelector('#request-service');
  const updateDescription = () => {
    document.querySelector('#selected-service-description').textContent = services.find(item => item.name === serviceSelect.value)?.description || '';
  };
  serviceSelect.addEventListener('change', updateDescription);
  updateDescription();
  document.querySelectorAll('[data-select-service]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    serviceSelect.value = link.dataset.selectService;
    updateDescription();
    document.querySelector('#request-form').scrollIntoView();
    serviceSelect.focus({ preventScroll: true });
  }));
}

const tourismData = document.querySelector('#tourism-data');
if (tourismData) {
  const experiences = JSON.parse(tourismData.textContent);
  const storageKey = 'socorro-destination-visit-v2';
  let plan = { selected: [], date: '' };
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey));
    if (saved && Array.isArray(saved.selected)) {
      plan.selected = [...new Set(saved.selected.filter(index => Number.isInteger(index) && experiences[index]))];
      plan.date = typeof saved.date === 'string' ? saved.date : '';
    }
  } catch { /* Private browsing or stale storage should not block planning. */ }
  const dateInput = document.querySelector('#visit-date');
  dateInput.value = plan.date;
  function renderPlan() {
    const list = document.querySelector('#visit-list');
    list.replaceChildren();
    plan.selected.forEach(index => {
      const row = document.createElement('li');
      const name = document.createElement('span');
      name.textContent = experiences[index].name;
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = '\u00d7';
      remove.setAttribute('aria-label', `Remove ${experiences[index].name}`);
      remove.title = `Remove ${experiences[index].name}`;
      remove.addEventListener('click', () => {
        plan.selected = plan.selected.filter(value => value !== index);
        renderPlan();
        document.querySelector(`[data-experience="${index}"]`).focus();
      });
      row.append(name, remove);
      list.append(row);
    });
    document.querySelectorAll('[data-experience]').forEach(button => {
      const selected = plan.selected.includes(Number(button.dataset.experience));
      button.setAttribute('aria-pressed', String(selected));
      button.textContent = selected ? 'Added to my visit \u2713' : 'Add to my visit +';
    });
    const count = plan.selected.length;
    document.querySelector('.planner-count').textContent = `${count} experience${count === 1 ? '' : 's'} selected`;
    document.querySelector('#visit-empty').hidden = count !== 0;
    document.querySelector('#download-plan').disabled = count === 0;
    document.querySelector('#clear-plan').disabled = count === 0 && !plan.date;
    try { localStorage.setItem(storageKey, JSON.stringify(plan)); } catch { /* Planning remains available without storage. */ }
  }
  document.querySelectorAll('[data-experience]').forEach(button => button.addEventListener('click', () => {
    const index = Number(button.dataset.experience);
    plan.selected = plan.selected.includes(index) ? plan.selected.filter(value => value !== index) : [...plan.selected, index];
    renderPlan();
  }));
  dateInput.addEventListener('change', () => { plan.date = dateInput.value; renderPlan(); });
  document.querySelector('#clear-plan').addEventListener('click', () => { plan = { selected: [], date: '' }; dateInput.value = ''; renderPlan(); });
  document.querySelector('#download-plan').addEventListener('click', () => {
    const content = ['MY SOCORRO ISLAND VISIT', 'Bucas Grande, Surigao del Norte', `Visit date: ${plan.date || 'To be decided'}`, '', ...plan.selected.map((index, order) => `${order + 1}. ${experiences[index].name}\n${experiences[index].description}`), '', 'Personal wish list, not a booking. Confirm availability with the tourism office.', `${window.location.origin}/services/?service=Tourism%20Assistance#request-form`].join('\n');
    const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'my-socorro-visit.txt'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  renderPlan();
}
