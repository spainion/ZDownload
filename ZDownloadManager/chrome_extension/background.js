// Service worker for ZDownloadManager Chrome integration.

chrome.downloads.onCreated.addListener((downloadItem) => {
  // Immediately cancel the browser download and forward to native app
  chrome.downloads.cancel(downloadItem.id);
  const port = chrome.runtime.connectNative('com.zdownloadmanager.host');
  port.postMessage({ url: downloadItem.url, dest: '' });
  port.onMessage.addListener((msg) => {
    console.log('ZDownloadManager response', msg);
  });
  port.onDisconnect.addListener(() => {
    const lastError = chrome.runtime.lastError;
    if (lastError) {
      console.error('Native messaging error', lastError.message);
    }
  });
});
