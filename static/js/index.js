const swiper = new Swiper('.swiper-container', {
    loop: true,
    autoplay: {
    delay: 3500,
    disableOnInteraction: false,
    },
    navigation: {
    nextEl: '.swiper-button-next',
    prevEl: '.swiper-button-prev',
    },
    pagination: {
    el: '.swiper-pagination',
    clickable: true,
    },
    effect: 'fade', // or 'slide', 'cube', 'coverflow', etc.
    fadeEffect: {
    crossFade: true
    }
});

// 햄버거버튼=>추천버튼 눌릴시
const toggleBtn = document.getElementById('menu-toggle');
const navMenu = document.getElementById('nav-menu');

toggleBtn.addEventListener('click', () => {
    navMenu.classList.toggle('show');
});

document.addEventListener("DOMContentLoaded", function () {
    const recommendLink = document.querySelector('.recommend-link'); // 추천 버튼만 타겟
    const loginAlert = document.getElementById("login-alert");
    const goToLogin = document.getElementById("go-to-login");
    const closeAlertBtn = document.getElementById("close-alert-btn");

        if (recommendLink) {
            recommendLink.addEventListener("click", function (e) {
                e.preventDefault(); // 실제 로그인 이동 막고 모달 띄움
                loginAlert.style.display = "flex";
            });
        }

        if (goToLogin) {
            goToLogin.addEventListener("click", function () {
                // 추천 버튼의 실제 href로 이동
                window.location.href = recommendLink.href;
            });
        }

        if (closeAlertBtn) {
            closeAlertBtn.addEventListener("click", function () {
                loginAlert.style.display = "none";
            });
        }
    });

  window.addEventListener('DOMContentLoaded', () => {
    const flash = document.querySelector('.flash-message');
    if (flash) {
      flash.style.opacity = 1;
      setTimeout(() => {
        flash.style.opacity = 0;
      }, 3000); // 3초 뒤 사라짐
    }
  });
