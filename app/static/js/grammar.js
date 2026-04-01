function loadQuestion() {
  fetch("/get_question/grammar")
    .then(res => res.json())
    .then(data => {
      currentQuestionId = data.id;
      document.getElementById("question").innerText = data.question;
    });
}

function submitAnswer(answer) {
  const startTime = performance.now();

  fetch("/submit_answer", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      question_id: currentQuestionId,
      answer: answer,
      response_time: (performance.now() - startTime) / 1000
    })
  })
  .then(res => res.json())
  .then(data => {
    console.log("New Ability:", data.new_ability);
    loadQuestion(); // next adaptive question
  });
}

(function(){

const BANK = [
{q:"She ____ to school every day.", options:["go","goes","going","gone"], answer:1, difficulty:"easy"},
{q:"They ____ playing outside.", options:["is","are","was","be"], answer:1, difficulty:"easy"},
{q:"I ____ a book yesterday.", options:["read","reads","reading","reader"], answer:0, difficulty:"easy"},
{q:"Neither the teacher nor the students ____ ready.", options:["is","are","was","be"], answer:1, difficulty:"medium"},
{q:"If she ____ earlier, she would catch the bus.", options:["leave","left","leaves","leaving"], answer:1, difficulty:"medium"},
{q:"He has been working here ____ 2019.", options:["for","since","from","during"], answer:1, difficulty:"medium"},
{q:"Rarely ____ such dedication.", options:["I have seen","have I seen","I seen","seen I"], answer:1, difficulty:"hard"},
{q:"Not only ____ late, but he also forgot his work.", options:["he was","was he","he is","is he"], answer:1, difficulty:"hard"},
{q:"Had she known, she ____ earlier.", options:["will leave","would leave","would have left","leaves"], answer:2, difficulty:"hard"}

];

let ability = 0
let questionCount = 0
let maxQuestions = 10

let startTime

function getDifficulty(){

if(ability <= -2) return "easy"
if(ability >= 2) return "hard"
return "medium"

}

function pickQuestion(){

let diff = getDifficulty()

let pool = BANK.filter(q => q.difficulty === diff)

return pool[Math.floor(Math.random()*pool.length)]

}

let current

function loadQuestion(){

if(questionCount >= maxQuestions){

finishTest()
return

}

current = pickQuestion()

document.getElementById("question").innerText = current.q
document.getElementById("qnum").innerText = questionCount+1

let optDiv = document.getElementById("options")
optDiv.innerHTML=""

current.options.forEach((opt,i)=>{

let btn = document.createElement("button")

btn.className="block w-full text-left border p-3 rounded hover:bg-gray-100"

btn.innerText=opt

btn.onclick=()=>answer(i)

optDiv.appendChild(btn)

})

startTime = Date.now()

}

function answer(choice){

let time = (Date.now() - startTime)/1000

if(choice === current.answer){

ability += 1

}else{

ability -= 1

}

questionCount++

loadQuestion()

}
function init(){
  // build difficulty pools
  easyPool = BANK.filter(b => b.difficulty === 'easy').slice();
  mediumPool = BANK.filter(b => b.difficulty === 'medium').slice();
  shuffle(easyPool); shuffle(mediumPool);
  document.getElementById('question-count').textContent = QUIZ_LENGTH;
  bindButtons();
  questionCount = 0; streak = 0; currentDifficulty = 'easy'; results = [];
  testStart = performance.now();
  loadQuestion();
}

function bindButtons(){
    document.getElementById('q-skip').addEventListener('click', onSkip);
    document.getElementById('q-answer').addEventListener('keydown', (e)=>{
    if(e.key === 'Enter') onNext();
  });
}

function finishTest(){

document.getElementById("question").innerHTML =
"Test Complete"

document.getElementById("options").innerHTML =
"Grammar Ability Score: <b>"+ability+"</b>"
 document.getElementById('numeracy-result').classList.remove('hidden');
  // hide question card
  document.getElementById('question-card').style.display = 'none';
  document.getElementById('q-next').style.display = 'none';
  document.getElementById('q-skip').style.display = 'none';
sendResults()

}


function sendResults(){

fetch("/api/grammar_results",{
method:"POST",
headers:{"Content-Type":"application/json"},
body:JSON.stringify({
score:ability,
questions:maxQuestions
})
})

}

loadQuestion()

})()