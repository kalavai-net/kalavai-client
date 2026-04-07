// scroll to the active link in the sidebar on page load
const sidebar = document.querySelector('[data-sidebar="content"]');
const activeLink = sidebar?.querySelector('[data-active="true"]');
if (sidebar && activeLink) {
	const saved = sessionStorage.getItem("sidebar-scroll");
	if (saved !== null) {
		// restore the last offset
		sidebar.scrollTop = parseInt(saved, 10);
	}
	activeLink.scrollIntoView({ block: "center", behavior: "smooth" });
	window.addEventListener("beforeunload", () => {
		// save the current offset of the sidebar to session storage so we can restore it on page load
		sessionStorage.setItem("sidebar-scroll", sidebar.scrollTop);
	});
}
