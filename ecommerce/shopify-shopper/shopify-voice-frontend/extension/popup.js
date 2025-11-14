// Inject hidden iframe to request microphone permission
const permFrame = document.createElement('iframe');
permFrame.hidden = true;
permFrame.allow = 'microphone';
permFrame.src = chrome.runtime.getURL('permission/index.html');
document.body.appendChild(permFrame);

window.addEventListener('message', (event) => {
  const data = event.data;

  console.log('popup.js received message:', event);

  // IMPORTANT: Always verify the origin of the message for security.

  // Case 1: Message from the permission iframe (extension's own origin)
  if (event.origin === chrome.runtime.getURL('').slice(0, -1)) { // Removes trailing slash for comparison
    console.log('Message from extension iframe detected');
    if (data && data.type === 'redirect' && data.url) {
      // This was the original logic, presumably for some internal extension redirect
      console.log('Sending redirect message to background.js:', data);
      chrome.runtime.sendMessage({ type: 'redirect', url: data.url });
      return; // Message handled
    }
  }

  // Case 2: Message from your Next.js app (running on localhost:3000 or your production domain)
  // IMPORTANT: Update 'http://localhost:3000' if your Next.js app is served from a different origin in production.
  if (event.origin === 'http://localhost:3000') { // Or your actual app's origin
    console.log('Message from Next.js app detected:', data);
    if (data && data.type === 'navigateFromNextJs' && data.url) {
      console.log('Message from Next.js app received in popup.js:', data);
      console.log('About to send actualNavigate message to background.js');
      chrome.runtime.sendMessage({ type: 'actualNavigate', url: data.url });
      console.log('chrome.runtime.sendMessage call completed');
      return; // Message handled
    }
    // You can add more 'else if' blocks here for other message types from your Next.js app
  }

  // Optional: Log unhandled or unexpected messages for debugging
  console.log('Unhandled/unexpected message in popup.js:', event);
});