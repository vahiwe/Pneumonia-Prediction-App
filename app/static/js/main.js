    let btn = document.getElementsByClassName("navButton");
    let navBar = document.getElementById("navBar");
    let header = document.getElementsByTagName("header")[0];
   let displayel= "none";
    btn[0].addEventListener("click", () => {
        if (displayel ==="none"){
           navBar.style.display = "flex";
           header.style.marginBottom = "120px"
           displayel = "flex";
        }
        else {
         navBar.style.display = "none";
         header.style.marginBottom = "0"
         displayel = "none"
        }
    })
