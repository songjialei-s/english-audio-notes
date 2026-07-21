App({
  globalData: {
    baseUrl: wx.getStorageSync('serverUrl') || 'http://10.0.5.165:8000'
  },
  setServerUrl(url) {
    this.globalData.baseUrl = url
    wx.setStorageSync('serverUrl', url)
  }
})
