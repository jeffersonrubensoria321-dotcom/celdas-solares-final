"""Animación temporal de paquetes de energía; acoplada al balance espectral."""
import json

def energy_animation(s):
    payload=json.dumps({'shares':[s['sub']/s['pin'],s['therm']/s['pin'],s['useful']/s['pin']]})
    return '''<!doctype html><html lang="es"><meta charset="utf-8"><style>
    body{margin:0;background:#0c1828;color:#e5edf5;font:14px Arial}canvas{width:100%;height:245px}
    button{background:#20344a;color:white;border:1px solid #7b93aa;border-radius:6px;padding:7px 18px;margin:8px 18px}
    </style><button id="toggle">Pausar animación</button><canvas id="c"></canvas>
    <script>const cfg=PAYLOAD;const cv=document.getElementById('c'),ctx=cv.getContext('2d');
    cv.width=1100;cv.height=245;let time=0,last=0,paused=false;
    const colors=['#9caabb','#f3a84c','#59d4bb'];
    const names=['No absorbida','Calor de termalización','Energía tras termalizar'];
    document.getElementById('toggle').onclick=function(){paused=!paused;this.textContent=paused?'Reanudar animación':'Pausar animación'};
    function paint(now){if(last&&!paused)time+=(now-last)/1000;last=now;
      ctx.clearRect(0,0,1100,245);ctx.font='15px Arial';ctx.fillStyle='#e5edf5';ctx.fillText('ENERGÍA SOLAR',20,30);
      ctx.fillStyle='#263b52';ctx.fillRect(330,40,70,170);ctx.fillStyle='white';ctx.fillText('Si',356,131);
      names.forEach((n,i)=>{ctx.fillStyle=colors[i];ctx.fillText(n+' · '+(100*cfg.shares[i]).toFixed(1)+' %',770,56+i*75)});
      for(let j=0;j<54;j++){const f=(j+.5)/54;let k=f<cfg.shares[0]?0:f<cfg.shares[0]+cfg.shares[1]?1:2;
       const phase=(time*.23+j/54)%1;let x,y;if(phase<.42){x=30+phase/.42*325;y=126+12*Math.sin(j)}
       else{x=355+(phase-.42)/.58*380;y=126+(k*75+50-126)*(phase-.42)/.58}
       ctx.beginPath();ctx.fillStyle=phase<.42?'#ffe5a0':colors[k];ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();}
      requestAnimationFrame(paint);}
    requestAnimationFrame(paint);</script></html>'''.replace('PAYLOAD',payload)
