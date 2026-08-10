// Runs before hydration so the correct theme class is on <html> for the
// very first paint — otherwise a dark-system-preference user would see a
// flash of the light theme until ThemeProvider's effect runs.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = window.localStorage.getItem("jarvis:theme");
    var theme = stored === "light" || stored === "dark"
      ? stored
      : (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    }
  } catch (_error) {
    // localStorage/matchMedia unavailable (e.g. privacy mode) - fall back
    // to the CSS prefers-color-scheme media query already in globals.css.
  }
})();
`;

export function ThemeScript() {
  return <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />;
}
