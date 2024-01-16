// edit profil
function update_profile() {
  let name = $("#username_update").val();
  let file = $("#picture")[0].files[0];
  let form_data = new FormData();
  form_data.append("file_give", file);
  form_data.append("longname_give", name);

  $.ajax({
    type: "POST",
    url: "/update_profile",
    data: form_data,
    cache: false,
    contentType: false,
    processData: false,
    success: function (response) {
      if (response["result"] === "success") {
        swal("Success",response["msg"],"success");
        window.location.reload();
      }
    },
  });
}

// logout
function sign_out() {
  $.removeCookie("mytoken", { path: "/" });
  swal("Signed out!");
  window.location.href = "/login/user";
}

// batal surat kelahiran

function batal(birthId) {
  $.ajax({
    url: '/user/delete_birth/' + birthId,
    type: 'POST',
    success: function(response) {
      if (response.result === 'success') {
        swal("Success","Permohonan berhasil dibatalkan","success");
        window.location.reload();
      } else {
        console.log('Failed to delete :', response.msg);
      }
    },
    error: function(xhr, status, error) {
      console.log('Error:', error);
    }
  });
}

// batal surat domisili

function hapus(domisiliId) {
  $.ajax({
    url: '/user/delete_domisili/' + domisiliId,
    type: 'POST',
    success: function(response) {
      if (response.result === 'success') {
        swal("Success","Permohonan berhasil dibatalkan","success");
        window.location.reload();
      } else {
        console.log('Failed to delete :', response.msg);
      }
    },
    error: function(xhr, status, error) {
      console.log('Error:', error);
    }
  });
}

// batal surat domisili

function cancel(dieId) {
  $.ajax({
    url: '/user/delete_die/' + dieId,
    type: 'POST',
    success: function(response) {
      if (response.result === 'success') {
        swal("Success","Permohonan berhasil dibatalkan","success");
        window.location.reload();
      } else {
        console.log('Failed to delete :', response.msg);
      }
    },
    error: function(xhr, status, error) {
      console.log('Error:', error);
    }
  });
}

