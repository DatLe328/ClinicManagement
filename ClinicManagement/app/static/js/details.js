function spinner(status="block") {
    let s = document.getElementsByClassName('my-spinner')
    for (let i = 0; i < s.length; i++)
        s[i].style.display = status
}

function loadComments(productId) {
    spinner()
    fetch(`/api/products/${productId}/comments`).then(res => res.json()).then(data => {
        spinner("none")
        let h = ""
        data.forEach(c => {
            h += `
                <li class="list-group-item">
                  <div class="row">
                      <div class="col-md-1 col-sm-4">
                          <img src="${c.user.avatar}"
                               alt="${c.user.name}" class="img-fluid rounded-circle" />
                      </div>
                      <div class="col-md-11 col-sm-8">
                          <p>${c.content}</p>
                          <small>Bình luận <span class="text-info">${moment(c.created_date).locale("vi").fromNow()}</span>  bởi <span class="text-info">${c.user.name}</span></small>
                      </div>
                  </div>
              </li>
            `
        })

        let d = document.getElementById("comments")
        d.innerHTML = h
    })
}

function addComment(productId) {
    spinner()
    fetch(`/api/products/${productId}/comments`, {
        method: "post",
        body: JSON.stringify({
            "content": document.getElementById("comment-content").value
        }),
        headers: {
            "Content-Type": "application/json"
        }
    }).then(res => res.json()).then((data) => {
        spinner("none")
       if (data.status === 204){
            let c = data.comment
            h = `
                <li class="list-group-item">
                  <div class="row">
                      <div class="col-md-1 col-sm-4">
                          <img src="${c.user.avatar}"
                               alt="${c.user.name}" class="img-fluid rounded-circle" />
                      </div>
                      <div class="col-md-11 col-sm-8">
                          <p>${c.content}</p>
                          <small>Bình luận <span class="text-info">${moment(c.created_date).locale("vi").fromNow()}</span>  bởi <span class="text-info">${c.user.name}</span></small>
                      </div>
                  </div>
              </li>
            `

             let d = document.querySelector("#comments > li:first-child")
             if (d != null)
                d.insertAdjacentHTML("beforebegin", h)
             else
                document.getElementById("comments").innerHTML = h
       } else
            alert("Hệ thống đang có lỗi!")
    }) // promise
}