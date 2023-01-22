const titleH3 = document.getElementById('titleH3');
const titleField = document.getElementById('title');
const primaryFeastNameField = document.getElementById('primary_feast_name');
const secondaryFeastNameField = document.getElementById('secondary_feast_name');
const dateField = document.getElementById('date');

const setTitle = () => {
  let txt;
  const primaryFeastName = primaryFeastNameField.options[primaryFeastNameField.selectedIndex].innerText;
  const secondaryFeastName = secondaryFeastNameField.options[secondaryFeastNameField.selectedIndex].innerText;
  if (secondaryFeastNameField.value)
    txt = primaryFeastName + ' (' + secondaryFeastName + ')';
  else
    txt = primaryFeastName;

  titleH3.innerText = txt;
  titleField.value = txt;
};

setTitle();
primaryFeastNameField.addEventListener('change', setTitle);
secondaryFeastNameField.addEventListener('change', setTitle);

const updateDateFromPrimaryFeast = async () => {
  const url = '/feast/api/' + primaryFeastNameField.value + '/date';
  const r = await fetch(url);
  const j = await r.json();
  if (j !== null)
    dateField.value = j;
};

await updateDateFromPrimaryFeast();
primaryFeastNameField.addEventListener('change', updateDateFromPrimaryFeast);

const today = new Date()
const day = 1000 * 60 * 60 * 24;  // milliseconds in a day
const sunday = new Date(today.getTime() + (7 - today.getDay()) * day);

function toISO(date) {
  return date.toISOString().split('T')[0];
}

const todayBtn = document.getElementById('today-btn');
todayBtn.onclick = () => {
  dateField.value = toISO(today);
};

const sundayBtn = document.getElementById('sunday-btn');
sundayBtn.onclick = () => {
  dateField.value = toISO(sunday);
};

const prevWeekBtn = document.getElementById('prev-week-btn');
prevWeekBtn.onclick = () => {
  const prevWeek = (new Date(dateField.value)).getTime() - 7 * day;
  dateField.value = toISO(new Date(prevWeek));
};

const nextWeekBtn = document.getElementById('next-week-btn');
nextWeekBtn.onclick = () => {
  const nextWeek = (new Date(dateField.value)).getTime() + 7 * day;
  dateField.value = toISO(new Date(nextWeek));
};

/**
 * Cause a class to be applied to the specified fields when the
 * specified element is mouseovered. Note that this overwrites
 * btn.onmouseover and btn.onmouseout, so it can only be used once
 * for each btn.
 *
 * @param btn the element that should highlight when mouseovered, probably a button
 * @param cls the class to apply, e.g. bg-warning
 * @param fields the elements that should be modified, probably input fields
 */
function highlightOnMouseover(btn, cls, fields) {
  btn.onmouseover = () => {
    fields.forEach((e) => {
      e.classList.add(cls)
    });
  };
  btn.onmouseout = () => {
    fields.forEach((e) => {
      e.classList.remove(cls)
    });
  };
}

highlightOnMouseover(todayBtn, 'bg-warning', [dateField]);
highlightOnMouseover(sundayBtn, 'bg-warning', [dateField]);
highlightOnMouseover(prevWeekBtn, 'bg-warning', [dateField]);
highlightOnMouseover(nextWeekBtn, 'bg-warning', [dateField]);

addTooltip(prevWeekBtn, '7 days earlier');
addTooltip(todayBtn, 'Set the date to today');
addTooltip(sundayBtn, 'Set the date to this Sunday');
addTooltip(nextWeekBtn, '7 days later');
