// Script data pengaduan 
function time2str(date) {
    let today = new Date();
    let time = (today - date) / 1000 / 60;  // minutes

    if (time < 60) {
        return parseInt(time) + " minutes ago";
    }
    time = time / 60;  // hours
    if (time < 24) {
        return parseInt(time) + " hours ago";
    }
    time = time / 24; // days
    if (time < 7) {
        return parseInt(time) + " days ago";
    }
    return `${date.getFullYear()}.${date.getMonth() + 1}.${date.getDate()}`;
}

function get_post(){
    $("#pills-pengaduan").empty()
    $.ajax({
        type: "GET",
        url : "/posting/pengaduan",
        data:{},
        success: function(response){
            if (response["result"] === "success") {
                let posts = response["posts"];
                for (let i = 0; i < posts.length; i++) {
                  let post = posts[i];
                  let time_post = new Date(post["tanggal_upload"]);
                  let time_before = time2str(time_post);

                  let html_temp =`<div class="card" id="${post["_id"]}" style="width: 400px;">
                  <div class="card-body">
                    <p class="card-text">Nama : ${post["name"]}</p>
                    <p class="card-text">Pengaduan : ${post["pengaduan"]}</p>
                    <p class="card-text">Tanggal Kejadian : ${post["tanggal_kejadian"]}</p>
                    <a style="float:right;" href="/download_pengaduan/${post["file"]}" type="button" class="btn btn-dark">Lihat Bukti Pengaduan</a>
                  </div>
                  <div class="card-footer text-body-secondary">
                  ${time_before}
                  </div>
              </div>`;

                $("#pills-pengaduan").append(html_temp);
                }
            }
        }
    });
}


  








