// Handle extension icon click to open side panel
chrome.action.onClicked.addListener((tab) => {
  chrome.sidePanel.open({ tabId: tab.id });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'redirect' && message.url) {
    // This was the original message handler, assuming it might open a new tab
    // or redirect the popup itself, which is less likely/useful for a new page.
    // For clarity, let's assume this also means opening a new tab.
    chrome.tabs.create({ url: message.url });
  }

  if (message.type === 'actualNavigate' && message.url) {
    console.log('actualNavigate message received in background.js:', message, 'from sender:', sender);

    // For side panel, we need to get the current active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0) {
        const activeTab = tabs[0];
        chrome.tabs.update(activeTab.id, { url: message.url });
        console.log(`Updated tab ${activeTab.id} to ${message.url}`);
      } else {
        console.warn('No active tab found, opening in new tab as fallback.');
        chrome.tabs.create({ url: message.url });
      }
    });

    return true; // Indicates you wish to send a response asynchronously (if you use sendResponse)
  }
});