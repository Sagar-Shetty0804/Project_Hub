let userScore = 0;
let compScore = 0;
const choices = document.querySelectorAll(".choice");

let resultMsg = document.querySelector("#msg");

const userScoreMsg = document.querySelector("#playerScore");
const compScoreMsg = document.querySelector("#compScore");

const resetBtn = document.querySelector("#reset");

const Animation = document.querySelectorAll(".showAnimation i");


const genCompChoice = () => {
    const option = ["rock","paper","scissor"];
    let random = Math.floor(Math.random()*3);
    return option[random];
};

const drawEvent = () =>{
    resultMsg.innerText = 'It is a Draw';


}

const userWin = (uC,cC) =>{
    resultMsg.innerText = `You won,${uC} beats ${cC}` ;
    userScore = userScore + 1;   
    userScoreMsg.innerText = userScore;
}

const compWin = (uC,cC) =>{
    resultMsg.innerText = `You lost,${cC} beats ${uC}`;
    compScore = compScore + 1;
    compScoreMsg.innerText = compScore;
}

const animate = () =>{
    Animation[0].animate(
        [
            {
                rotate: "z 90deg"
            },
            {
                rotate: "z 40deg"
            },
            {
                rotate: "z 90deg"
                
            }
        ],
        {
            duration:900,
            iterations:3,
        }
    )

    Animation[1].animate(
        [
            {
                rotate: "1 1 0 180deg" 
            },
            {
                rotate: "1 1.6 0 180deg"
            },
            {
                rotate: "1 1 0 180deg "
            }
        ],
        {
            duration:900,
            iterations:3,
        }
    )


} 

const newClassName = (Choice) =>{
    if(Choice === "rock"){
        return "fa-regular fa-hand-back-fist"
    }else if(Choice === "paper"){
        return "fa-regular fa-hand"
    }else{
        return "fa-regular fa-hand-scissors"
    }
}

const playGame = (userChoice) =>{
    const compChoice = genCompChoice();
    
    animate();

    

    setTimeout(() =>{

        Animation[0].className = newClassName(userChoice);
        Animation[1].className = newClassName(compChoice);
        if(userChoice === compChoice){
            drawEvent();
        }
        else if(
            userChoice === "rock" && compChoice === "scissor" ||
            userChoice === "paper" && compChoice === "rock" ||
            userChoice === "scissor" && compChoice === "paper" 
        ){
            userWin(userChoice,compChoice);
        }
        else{
            compWin(userChoice,compChoice);
        }
    },3150)  



};

choices.forEach((choice) => {
    choice.addEventListener("click", () =>{
        
        const userAction = choice.getAttribute("id");

        playGame(userAction)
    })    
});

resetBtn.addEventListener("click", () =>{


    userScore = 0;
    compScore = 0;
    userScoreMsg.innerText = userScore;
    compScoreMsg.innerText = compScore;
    Animation[0].className = "fa-regular fa-hand-back-fist";
    Animation[1].className = "fa-regular fa-hand-back-fist";
    resultMsg.innerText = 'Play your move';
})



