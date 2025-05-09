// C:\Users\facec\Desktop\smart_city\static\js\register.js

// 생년월일을 주민등록번호 앞자리로 삽입
function updateRegNumber() {
    var birthday = document.getElementById("birthday").value;
    if (birthday) {
        var regNumber = birthday.replace(/-/g, "").substring(2);
        document.getElementById("regNumberInput").value = regNumber;
    }
}

// 입력된 주민등록번호 뒷자리 첫번째 숫자를 통해 성별 추출
function getGenderFromRegNumber(regNumberSuffix) {
    var genderDigit = parseInt(regNumberSuffix.charAt(0), 10);
    return genderDigit % 2 === 0 ? 'female' : 'male';
}

function handleSubmit(event) {
    // 주민등록번호와 성별 데이터 설정
    var regNumberPrefix = document.getElementById("regNumberInput").value;
    var regNumberSuffix = document.getElementById("regNumberInput2").value;
    var totalRegNumber = regNumberPrefix + "-" + regNumberSuffix;
    var gender = getGenderFromRegNumber(regNumberSuffix);

    document.getElementById("genderField").value = gender;
    document.getElementById("totalRegNumberField").value = totalRegNumber;
}

// input에 입력시 실시간으로 유효성 검사
document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordError = document.getElementById('passwordError');
    const confirmPasswordError = document.getElementById('password_confirmError');
    const regNumberInput = document.getElementById('regNumberInput2');
    const regNumberError = document.getElementById('regNumberError');
    const birthdayInput = document.getElementById('birthday');
    const birthdayError = document.getElementById('birthdayError');
    const dayError = document.getElementById('dayError');

    // 비밀번호 실시간 검증
    passwordInput.addEventListener('input', function () {
        const password = this.value;
        const hasTwoNumbers = (password.match(/\d/g) || []).length >= 2;
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        if (!hasTwoNumbers || !hasSpecialChar) {
            passwordError.style.display = 'block';
        } else {
            passwordError.style.display = 'none';
        }
    });

    // 비밀번호, 비밀번호 확인 일치여부 실시간 검사
    confirmPasswordInput.addEventListener('input', function () {
        const password = passwordInput.value;
        const confirmPassword = this.value;

        if (password !== confirmPassword) {
            confirmPasswordError.style.display = 'block';
        } else {
            confirmPasswordError.style.display = 'none';
        }
    });

    // 주민등록번호 유효성 실시간 검사
    regNumberInput.addEventListener('input', function () {
        const regNumberSuffix = this.value;
        const regNumberFirstDigit = parseInt(regNumberSuffix.charAt(0), 10);

        if (regNumberFirstDigit > 4 || regNumberFirstDigit == 0) {
            regNumberError.style.display = 'block';
        } else {
            regNumberError.style.display = 'none';
        }
    });

    // 생년월일 유효성 검사
    birthdayInput.addEventListener('input', function () {
        const birthday = new Date(this.value);
        const today = new Date();
    
        today.setHours(0, 0, 0, 0);
        birthday.setHours(0, 0, 0, 0);
    
        // 미래 날짜인지 확인 → 유효한 날짜 오류 (dayError)
        if (birthday > today) {
            dayError.style.display = 'block';
        } else {
            dayError.style.display = 'none';
        }
    
        // 나이 계산 → 18세 이상 100세 이하만 허용
        let age = today.getFullYear() - birthday.getFullYear();
        const monthDifference = today.getMonth() - birthday.getMonth();
    
        if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthday.getDate())) {
            age--;
        }
    
        // 나이 조건 검사 → 18세 미만 또는 100세 초과는 birthdayError로 표시
        if (age < 18 || age > 100) {
            birthdayError.style.display = 'block';
        } else {
            birthdayError.style.display = 'none';
        }
    
        // 날짜와 나이 둘 다 유효할 때만 주민등록번호 앞자리 자동 완성
        if (dayError.style.display === 'none' && birthdayError.style.display === 'none') {
            updateRegNumber();
        }
    });

    // 폼 제출 이벤트 핸들러
    form.addEventListener('submit', function (event) {
        // 주민등록번호 및 성별 필드 자동 설정
        handleSubmit(event);

        const hasError = 
            dayError.style.display === 'block' || 
            birthdayError.style.display === 'block' || 
            passwordError.style.display === 'block' || 
            confirmPasswordError.style.display === 'block' || 
            regNumberError.style.display === 'block';

        if (hasError) {
            event.preventDefault(); // 오류가 있으면 제출 막기
            alert("입력 오류가 있습니다. 확인 후 다시 시도해주세요.");
        }
    });
});

// 주소 검색 팝업 띄우기
function openAddressSearch() {
    new daum.Postcode({
        oncomplete: function(data) {
            var fullAddress = data.address;
            var extraAddress = '';

            if (data.addressType === 'R') {
                if (data.bname !== '') {
                    extraAddress += data.bname;
                }
                if (data.buildingName !== '') {
                    extraAddress += (extraAddress !== '' ? ', ' + data.buildingName : data.buildingName);
                }
                fullAddress += extraAddress !== '' ? ' (' + extraAddress + ')' : '';
            }

            document.getElementById('address').value = fullAddress;
        }
    }).open();
}

