const tickets = [
  {id:101,title:'Ноутбук Lenovo',issue:'Не заряжается после замены блока питания',customer:'Ирина К.',status:'Диагностика',priority:'Важная',estimate:'3 500 ₽',next:'Проверить разъём питания'},
  {id:102,title:'Телефон Samsung',issue:'Треснуло защитное стекло',customer:'Антон М.',status:'Новая',priority:'Обычная',estimate:'1 200 ₽',next:'Принять на осмотр'},
  {id:103,title:'Монитор LG',issue:'Изображение пропадает через несколько минут',customer:'Мария С.',status:'В работе',priority:'Срочная',estimate:'5 800 ₽',next:'Завершить ремонт платы'},
  {id:104,title:'Планшет iPad',issue:'Не работает кнопка питания',customer:'Олег В.',status:'Готово',priority:'Обычная',estimate:'2 400 ₽',next:'Связаться с клиентом'},
  {id:105,title:'Игровая приставка',issue:'Перегревается при запуске игры',customer:'Дмитрий Н.',status:'В работе',priority:'Важная',estimate:'4 100 ₽',next:'Проверить систему охлаждения'},
];
const list=document.querySelector('#tickets'), detail=document.querySelector('#detail');
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
render();

