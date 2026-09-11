import "./Button.css";
const Button = ({ text, color, onClick }) => {
  console.log(text);
  console.log(color);
  return (
    <>
      <div className={`btn ${color===undefined?"":color}`} onClick={onClick}>{`${text==='로그인'?text+'💚':text}`}</div>
      
      {text==="로그인" && <div>{text} 집에가고싶어 </div>}
       {text==="로그인" && <div>{text} 한화생명 파이팅 내일 이기자  </div>}
    </>
  );
};
export default Button;
