(function () {
  var script = document.currentScript;
  var key = script.getAttribute("data-user-key") || "user_id";

  function getCookie(name) {
    var match = document.cookie.match(
      new RegExp("(?:^|; )" + name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)")
    );
    return match ? decodeURIComponent(match[1]) : null;
  }

  var userId = localStorage.getItem(key) || getCookie(key);
  if (!userId) return;

  var userHash = script.getAttribute("data-user-hash") || "";
  var baseUrl = new URL(script.src).origin;

  // Check parent-side flag: was the user connected before this page load?
  var wasConnected = localStorage.getItem("voice_widget_connected") === "true";

  var container = document.createElement("div");
  container.style.cssText =
    "position:fixed;bottom:1.25rem;right:1.25rem;width:280px;height:130px;" +
    "border-radius:0.75rem;overflow:hidden;z-index:10000;" +
    "box-shadow:0 8px 32px rgba(0,0,0,0.4);border:1px solid #334155;";

  var iframe = document.createElement("iframe");
  var src = baseUrl + "/widget.html?user_id=" + encodeURIComponent(userId);
  if (userHash) src += "&user_hash=" + encodeURIComponent(userHash);
  if (wasConnected) src += "&auto_connect=true";
  iframe.src = src;
  iframe.allow = "microphone; autoplay";
  iframe.style.cssText = "width:100%;height:100%;border:none;";

  container.appendChild(iframe);
  document.body.appendChild(container);

  // Listen for connect/disconnect signals from the widget iframe
  window.addEventListener("message", function (event) {
    if (event.source !== iframe.contentWindow) return;
    if (event.data === "voice-connected") {
      localStorage.setItem("voice_widget_connected", "true");
    } else if (event.data === "voice-disconnected") {
      localStorage.removeItem("voice_widget_connected");
    }
  });
})();
