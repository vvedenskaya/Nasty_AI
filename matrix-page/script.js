var q=document.getElementById('matrix'),
        s=window.screen,
        w=q.width=s.width,
        h=q.height=s.height,
        p=Array(256).join(1).split(''),
        c=q.getContext('2d'),
        m=Math;

setInterval(function(){
   c.fillStyle= 'rgba(0,0,0,0.05)';
     c.fillRect(0,0,w,h);
     c.fillStyle='rgba(0,255,0,1)';
     p=p.map(function(v,i){
        r=m.random();
        var str =  String.fromCharCode(m.floor(2720+r*33));
        c.fillText(str,i*10,v);
        v+=10;
        var ret = v>768+r*1e4?0:v
        return ret;

    });
},33);




