
// Active menu + year
(function(){
  const path = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.menu a').forEach(a=>{ if(a.getAttribute('href')===path) a.classList.add('active'); });
  const y=document.getElementById('y'); if(y) y.textContent=new Date().getFullYear();
})();
// Reveal on scroll
(function(){
  const els = document.querySelectorAll('.reveal');
  const io  = new IntersectionObserver((es)=>{ es.forEach(e=>{ if(e.isIntersecting){ e.target.classList.add('show'); io.unobserve(e.target);} }); }, {rootMargin:"-10% 0px -10% 0px"});
  els.forEach(el=>io.observe(el));
})();
// Carousel
(function(){
  const track = document.querySelector('.track'); if(!track) return;
  const slides = Array.from(track.children);
  const dots = Array.from(document.querySelectorAll('.dot'));
  let i = 0;
  function go(n){ i=(n+slides.length)%slides.length; track.style.transform=`translateX(${-i*100}%)`; dots.forEach((d,k)=>d.classList.toggle('active',k===i)); }
  dots.forEach((d,k)=>d.addEventListener('click',()=>go(k)));
  setInterval(()=>go(i+1), 5200); go(0);
})();
// Simple cart in localStorage
const Cart = {
  key:'vu_cart',
  get(){ try{return JSON.parse(localStorage.getItem(this.key)||'[]')}catch(e){return []}},
  set(v){ localStorage.setItem(this.key, JSON.stringify(v)); Cart.renderCount(); },
  add(item){ const c=this.get(); c.push(item); this.set(c); },
  count(){ return this.get().length; },
  renderCount(){ document.querySelectorAll('[data-cart-count]').forEach(el=>el.textContent=this.count()); }
};
document.addEventListener('click', (e)=>{
  const add = e.target.closest('[data-add]');
  if(add){ e.preventDefault(); const id=add.getAttribute('data-add'); const name=add.getAttribute('data-name'); Cart.add({id,name,qty:1}); alert('Agregado al carrito: '+name); }
});
window.addEventListener('DOMContentLoaded', Cart.renderCount);
// Search redirect from topbar
document.addEventListener('keydown', (e)=>{
  const box = document.querySelector('.search input'); if(document.activeElement===box && e.key==='Enter'){ location.href='buscar.html?q='+encodeURIComponent(box.value.trim()); }
});
// Search page filtering
function runSearch(){
  const params=new URLSearchParams(location.search); const q=(params.get('q')||'').toLowerCase();
  const i=document.getElementById('q'); if(i){ i.value=q; i.addEventListener('input',()=>{ filter(i.value.toLowerCase());}); }
  function filter(val){
    document.querySelectorAll('[data-item]').forEach(card=>{
      const text=(card.getAttribute('data-item')||'').toLowerCase();
      card.style.display = text.includes(val)?'':'none';
    });
  }
  filter(q);
}
