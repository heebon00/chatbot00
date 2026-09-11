import { useState } from "react";
const Card = () => {
  const [on, setOn] = useState(false);
  return ( 
    <>
       <h1 onClick={() => setOn((prev) => !prev)}>{on ? "🌞" : "🌜"}</h1>
      {console.log(on)}
      {/* on 이 true일때만 보이게  */}
      {/* !a 단항연산자 */}
      {/* a&&b,a||b 이항연산자 */}
      {/* a?b:c 삼항연산자 */}
      <div style={{ color: on ? "red" : undefined }}>Card</div></>
  );
};
export default Card;
