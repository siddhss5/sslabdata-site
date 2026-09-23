// Filters the works list on /publications/. The page lists every work
// without this script; the script reveals the filter form, applies the
// filters named in the URL (?year=, ?type=, ?project=, ?person=, ?q=) and
// writes the form's state back to the URL, so a filtered view can be shared.
(function () {
  var form = document.getElementById('works-filter');
  if (!form) return;
  var count = document.getElementById('works-filter-count');
  var entries = Array.prototype.slice.call(document.querySelectorAll('.pub-entry'));
  var sections = Array.prototype.slice.call(
    document.querySelectorAll('.pub-year-section, .pub-category-section'));

  function has(list, value) {
    return list.split(' ').indexOf(value) !== -1;
  }

  // One test per URL parameter, on the data attributes of an entry.
  var tests = {
    year: function (e, v) { return e.getAttribute('data-year') === v; },
    type: function (e, v) { return e.getAttribute('data-type') === v; },
    project: function (e, v) { return has(e.getAttribute('data-projects'), v); },
    person: function (e, v) { return has(e.getAttribute('data-people'), v); },
    q: function (e, v) { return e.getAttribute('data-searchable').indexOf(v.toLowerCase()) !== -1; }
  };
  var names = Object.keys(tests);

  function apply(state) {
    var shown = 0;
    entries.forEach(function (e) {
      e.hidden = !names.every(function (n) { return !state[n] || tests[n](e, state[n]); });
      if (!e.hidden) shown++;
    });
    sections.forEach(function (s) {
      s.hidden = !Array.prototype.some.call(s.querySelectorAll('.pub-entry'),
        function (e) { return !e.hidden; });
    });
    count.textContent = 'Showing ' + shown + ' of ' + entries.length + ' works';
  }

  // The URL is the state: an unknown value matches nothing rather than
  // being dropped, so a shared link shows what it names.
  var params = new URLSearchParams(location.search);
  var state = {};
  names.forEach(function (n) {
    state[n] = (params.get(n) || '').trim();
    form.elements[n].value = state[n];
  });
  apply(state);

  form.addEventListener('input', function () {
    var params = new URLSearchParams();
    names.forEach(function (n) {
      state[n] = form.elements[n].value.trim();
      if (state[n]) params.set(n, state[n]);
    });
    var query = params.toString();
    history.replaceState(null, '', location.pathname + (query ? '?' + query : ''));
    apply(state);
  });
  form.addEventListener('submit', function (event) { event.preventDefault(); });
  form.hidden = false;
})();
