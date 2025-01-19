$(document).ready(function() {
    $("div.bt-confirm > input").click(function() {
        $("div.confirm-click > div.confirm-info").show()
        $("div.confirm-click > div.confirm-info").fadeOut(3000)
    })
})

window.onload = function() {
    drawRevenueStats(labels, data)
  }