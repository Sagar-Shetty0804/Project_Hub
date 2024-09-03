let boxes = document.querySelectorAll(".box");
let reset_btn = document.querySelector("#reset");
let winner = document.createElement("p")
let turnX = true;


let h = document.querySelector("h1");


const winni = [
    [0, 1, 2],
    [0, 3, 6],
    [0, 4, 8],
    [1, 4, 7],
    [2, 5, 8],
    [2, 4, 6],
    [3, 4, 5],
    [6, 7, 8],
];

const enableFunction = () =>{
     for(let box of boxes){
        box.disabled = false;
     }       
}
const disableFunction = () =>{
     for(let box of boxes){
        box.disabled = true;
     }       
}

boxes.forEach((box) =>{
    box.addEventListener("click",() =>{
        if (turnX ===true){
            box.innerText = "X";
            turnX = false;
            
        }else{
            box.innerText = "O";
            turnX = true;
        }
        box.setAttribute("disabled","");
        checkWinner();
        
    })
});
//let win = false

const checkWinner = () =>{

    for(let pat of winni){
        // console.log(pat[0],pat[1],pat[2])
        // console.log(boxes[pat[0]].innerText,boxes[pat[1]].innerText,boxes[pat[2]].innerText)

        let pos1 = boxes[pat[0]].innerText;
        let pos2 = boxes[pat[1]].innerText;
        let pos3 = boxes[pat[2]].innerText;

        if(pos1 !="" && pos2 !="" && pos3 !=""){
            if(pos1 == pos2 && pos2 == pos3){
                winner.innerText = `Winner ${pos1}`;
                h.append(winner);
                disableFunction();
                
            }
        };

    };
};

reset_btn.addEventListener("click",() =>{
    enableFunction();
    for(let box of boxes){
        box.innerText = "";
    }
    winner.remove()
});
