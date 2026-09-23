const tickets = [
  {id:101,title:'Ноутбук Lenovo',issue:'Не заряжается после замены блока питания',customer:'Ирина К.',status:'Диагностика',priority:'Важная',estimate:'3 500 ₽',next:'Проверить разъём питания'},
  {id:102,title:'Телефон Samsung',issue:'Треснуло защитное стекло',customer:'Антон М.',status:'Новая',priority:'Обычная',estimate:'1 200 ₽',next:'Принять на осмотр'},
  {id:103,title:'Монитор LG',issue:'Изображение пропадает через несколько минут',customer:'Мария С.',status:'В работе',priority:'Срочная',estimate:'5 800 ₽',next:'Завершить ремонт платы'},
  {id:104,title:'Планшет iPad',issue:'Не работает кнопка питания',customer:'Олег В.',status:'Готово',priority:'Обычная',estimate:'2 400 ₽',next:'Связаться с клиентом'},
  {id:105,title:'Игровая приставка',issue:'Перегревается при запуске игры',customer:'Дмитрий Н.',status:'В работе',priority:'Важная',estimate:'4 100 ₽',next:'Проверить систему охлаждения'},
  {id:106,title:'Ноутбук ASUS',issue:'Шумит вентилятор и отключается под нагрузкой',customer:'Елена Р.',status:'Диагностика',priority:'Срочная',estimate:'4 600 ₽',next:'Проверить охлаждение'},
  {id:107,title:'Фотоаппарат Canon',issue:'Не открывается крышка батарейного отсека',customer:'Виктор П.',status:'Новая',priority:'Обычная',estimate:'900 ₽',next:'Принять на диагностику'},
  {id:108,title:'Моноблок HP',issue:'Медленно загружается система',customer:'Наталья Д.',status:'Готово',priority:'Важная',estimate:'3 800 ₽',next:'Согласовать выдачу'},
];
const list=document.querySelector('#tickets'), detail=document.querySelector('#detail');
function renderOverview(){
  const metrics=[['Всего заявок',tickets.length],['В работе',tickets.filter(t=>t.status==='В работе').length],['Срочных',tickets.filter(t=>t.priority==='Срочная').length],['Готово к выдаче',tickets.filter(t=>t.status==='Готово').length]];
  const metricBox=document.querySelector('#metrics');metricBox.replaceChildren();
  for(const [label,value] of metrics){const item=document.createElement('div');item.className='demo-metric';const caption=document.createElement('span');caption.textContent=label;const number=document.createElement('strong');number.textContent=value;item.append(caption,number);metricBox.append(item);}
  const breakdown=document.querySelector('#breakdown');breakdown.replaceChildren();
  for(const status of ['Новая','Диагностика','В работе','Готово']){const count=tickets.filter(t=>t.status===status).length;const row=document.createElement('div');row.className='breakdown-row';const label=document.createElement('span');label.textContent=status;const track=document.createElement('span');track.className='breakdown-track';const bar=document.createElement('span');bar.style.width=`${count/tickets.length*100}%`;track.append(bar);const value=document.createElement('strong');value.textContent=count;row.append(label,track,value);breakdown.append(row);}
}
function render(){
  const q=document.querySelector('#search').value.trim().toLocaleLowerCase('ru');
  const status=document.querySelector('#status').value, priority=document.querySelector('#priority').value;
  const shown=tickets.filter(t=>(!q||`${t.id} ${t.title} ${t.customer} ${t.issue}`.toLocaleLowerCase('ru').includes(q))&&(!status||t.status===status)&&(!priority||t.priority===priority));
  document.querySelector('#count').textContent=`Найдено: ${shown.length}`;list.replaceChildren();
  if(!shown.length){const empty=document.createElement('p');empty.className='empty';empty.textContent='По этим условиям заявок нет.';list.append(empty);return;}
  for(const t of shown){const button=document.createElement('button');button.type='button';button.className='ticket';
    const a=document.createElement('span');const title=document.createElement('strong');title.textContent=t.title;const number=document.createElement('small');number.textContent=`Заявка #${t.id} · ${t.priority}`;a.append(title,number);
    const b=document.createElement('span');b.textContent=t.customer;
    const c=document.createElement('span');c.className=`status ${t.status==='Готово'?'ready':t.status==='Новая'?'new':''}`;c.textContent=t.status;
    button.append(a,b,c);button.onclick=()=>open(t);list.append(button);}
}
function open(t){const content=document.querySelector('#detail-content');content.replaceChildren();const title=document.createElement('h2');title.textContent=t.title;content.append(title);const table=document.createElement('dl');for(const [label,value] of [['Номер',`#${t.id}`],['Клиент',t.customer],['Статус',t.status],['Приоритет',t.priority],['Проблема',t.issue],['Оценка',t.estimate],['Следующий шаг',t.next]]){const dt=document.createElement('dt');dt.textContent=label;const dd=document.createElement('dd');dd.textContent=value;table.append(dt,dd);}content.append(table);detail.hidden=false;document.querySelector('#close').focus();}
document.querySelector('#filters').addEventListener('input',render);
document.querySelector('#close').onclick=()=>{detail.hidden=true;};
document.addEventListener('keydown',event=>{if(event.key==='Escape')detail.hidden=true;});
renderOverview();render();
