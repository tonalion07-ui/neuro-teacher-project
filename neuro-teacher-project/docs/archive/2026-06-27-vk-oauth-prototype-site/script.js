/* =========================================================
   Content-agent — клиентский JS
   - Плавная прокрутка к якорям (учитывает sticky-шапку)
   - Sticky-кнопка Telegram: показывается после прокрутки за Hero
   - Без зависимостей. defer в index.html гарантирует порядок.
   ========================================================= */

(function () {
  "use strict";

  // ---------- 1. Плавная прокрутка с учётом sticky-шапки ----------
  // CSS scroll-padding-top уже сдвигает якорь, но мы дополнительно
  // снимаем залипание фокуса на ссылке, чтобы клавиатурная навигация
  // оставалась предсказуемой.
  function handleAnchorClick(event) {
    const link = event.target.closest('a[href^="#"]');
    if (!link) return;

    const href = link.getAttribute("href");
    if (!href || href === "#") return;

    const target = document.querySelector(href);
    if (!target) return;

    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });

    // Убираем hash из URL, чтобы не путать кнопки «Назад»
    if (history.replaceState) {
      history.replaceState(null, "", window.location.pathname + window.location.search);
    }
    // Снимаем фокус с самой ссылки после прокрутки
    setTimeout(() => link.blur(), 600);
  }

  document.addEventListener("click", handleAnchorClick);

  // ---------- 2. Sticky-кнопка ----------
  const stickyCta = document.querySelector(".sticky-cta");
  const hero = document.querySelector("#hero");

  if (stickyCta && hero) {
    // Показываем кнопку, когда верх hero уехал за верх экрана.
    function updateStickyCta() {
      const heroBottom = hero.getBoundingClientRect().bottom;
      const shouldShow = heroBottom < 0;
      if (shouldShow) {
        stickyCta.hidden = false;
        // Даём браузеру кадр на отрисовку до анимации transform
        requestAnimationFrame(() => stickyCta.classList.add("is-visible"));
      } else {
        stickyCta.classList.remove("is-visible");
        // Скрываем только после завершения transition (220ms)
        setTimeout(() => {
          if (!stickyCta.classList.contains("is-visible")) {
            stickyCta.hidden = true;
          }
        }, 250);
      }
    }

    // rAF — не чаще одного раза за кадр
    let ticking = false;
    window.addEventListener(
      "scroll",
      function () {
        if (!ticking) {
          requestAnimationFrame(function () {
            updateStickyCta();
            ticking = false;
          });
          ticking = true;
        }
      },
      { passive: true }
    );

    // Первичный расчёт — на случай, если страница открыта уже
    // прокрученной (например, при перезагрузке с якорным URL).
    updateStickyCta();
  }
})();
