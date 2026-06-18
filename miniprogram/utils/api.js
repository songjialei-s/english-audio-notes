const app = getApp()

export function uploadPDF(filePath) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: app.globalData.baseUrl + '/upload',
      filePath,
      name: 'file',
      success: (res) => resolve(JSON.parse(res.data)),
      fail: reject
    })
  })
}

export function getAudioUrl(filename) {
  return app.globalData.baseUrl + filename
}
