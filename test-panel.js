(()=>{
const admin=document.getElementById('admin');if(!admin)return;
const section=document.createElement('section');section.className='card';section.style.cssText='margin:24px 0;padding:22px;border-radius:5px';
section.innerHTML=`<h2>서버·DB 연결 테스트 (V57)</h2><p class="note">기존 신청 기능은 브라우저 데모 그대로입니다. 아래는 별도의 서버 공유 테스트 기록이며 실제 고객 정보는 입력하지 마세요.</p><p id="dbHealth">서버 연결 확인 중…</p><label>관리자 테스트 토큰 <input id="dbToken" type="password" autocomplete="off" placeholder="서버 실행 화면에 표시된 토큰" style="width:100%;padding:12px;border:1px solid #ddd"></label><div style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0"><button id="dbCreate" type="button">가상 신청 저장</button><button id="dbRefresh" type="button" class="secondary">DB 기록 불러오기</button></div><div id="dbResult" aria-live="polite"></div><div id="dbList"></div>`;
admin.append(section);
const el=id=>document.getElementById(id),safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path,method='GET',body){const r=await fetch(path,{method,headers:{'Content-Type':'application/json','X-Test-Admin-Token':el('dbToken').value},body:body?JSON.stringify(body):undefined});const x=await r.json();if(!r.ok)throw Error(x.error||'서버 오류');return x}
async function refresh(){try{const x=await api('/api/orders');el('dbList').innerHTML=x.orders.map(o=>`<div style="padding:12px;border:1px solid #ddd;margin:8px 0"><b>${safe(o.id)}</b> · ${safe(o.model)} · ${safe(o.carrier)} · ${safe(o.kind)}<br><select data-id="${safe(o.id)}">${['접수','해피콜 및 상담','개통 진행','배송','완료','취소'].map(s=>`<option ${s===o.status?'selected':''}>${s}</option>`).join('')}</select></div>`).join('')||'<p>서버에 기록이 없습니다.</p>';el('dbResult').textContent=`DB 기록 ${x.orders.length}건 조회 완료`}catch(e){el('dbResult').textContent=e.message}}
el('dbCreate').onclick=async()=>{try{const x=await api('/api/orders','POST',{model:'갤럭시 테스트 모델',carrier:'KT',kind:'번호이동'});el('dbResult').textContent='서버 저장 성공: '+x.id;await refresh()}catch(e){el('dbResult').textContent=e.message}};
el('dbRefresh').onclick=refresh;
el('dbList').onchange=async e=>{if(!e.target.matches('select[data-id]'))return;try{await api('/api/orders/'+e.target.dataset.id,'PATCH',{status:e.target.value});el('dbResult').textContent='서버 상태 변경 완료'}catch(err){el('dbResult').textContent=err.message}};
fetch('/api/health').then(r=>r.ok?r.json():Promise.reject()).then(()=>el('dbHealth').textContent='● 서버 및 SQLite 연결됨').catch(()=>el('dbHealth').textContent='○ 서버 미연결: index.html 직접 열기 대신 Python 서버 주소로 접속하세요');
})();
