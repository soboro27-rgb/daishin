const generateBtn = document.getElementById('generate-btn');
const numbersContainer = document.getElementById('numbers');

generateBtn.addEventListener('click', () => {
    generateLottoNumbers();
});

function generateLottoNumbers() {
    const numbers = [];
    while (numbers.length < 6) {
        const randomNumber = Math.floor(Math.random() * 45) + 1;
        if (!numbers.includes(randomNumber)) {
            numbers.push(randomNumber);
        }
    }
    numbers.sort((a, b) => a - b);
    displayNumbers(numbers);
}

function displayNumbers(numbers) {
    numbersContainer.innerHTML = '';
    for (const number of numbers) {
        const numberDiv = document.createElement('div');
        numberDiv.classList.add('number');
        numberDiv.textContent = number;
        numbersContainer.appendChild(numberDiv);
    }
}
