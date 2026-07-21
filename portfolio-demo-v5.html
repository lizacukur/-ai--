<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Елизавета — AI-креатор & веб-дизайнер</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  @font-face{
    font-family: 'Bounded';
    src: url('./fonts/Bounded-Regular.ttf') format('truetype');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
  }
  @font-face{
    font-family: 'Bounded';
    src: url('./fonts/Bounded-SemiBold.otf') format('opentype');
    font-weight: 600;
    font-style: normal;
    font-display: swap;
  }
  @font-face{
    font-family: 'Bounded';
    src: url('./fonts/Bounded-Variable.ttf') format('truetype-variations');
    font-weight: 100 900;
    font-style: normal;
    font-display: swap;
  }
  :root{
    --bg: #0D1320;
    --bg-elevated: #161D2C;
    --bg-elevated-2: #1D2536;
    --border: rgba(255,255,255,0.08);
    --orange: #FF7A33;
    --orange-soft: #FFB37A;
    --amber: #FFD9A8;
    --ink: #F2F0EB;
    --ink-muted: #8B93A6;
    --radius: 20px;
    --ease: cubic-bezier(.22,.61,.36,1);
  }

  *{ box-sizing: border-box; }
  html{ scroll-behavior: smooth; }
  body{
    margin:0;
    background: var(--bg);
    color: var(--ink);
    font-family: Arial, Helvetica, sans-serif;
    letter-spacing: -0.02em;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }
  a{ color: inherit; }

  .display{
    font-family: 'Bounded', sans-serif;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.01em;
  }
  .eyebrow{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--orange-soft);
  }

  a:focus-visible, button:focus-visible{
    outline: 2px solid var(--orange);
    outline-offset: 4px;
    border-radius: 4px;
  }

  .bg-fx{
    position: fixed; inset:0; z-index:-2;
    background:
      radial-gradient(700px 500px at 85% -5%, rgba(255,122,51,0.16), transparent 60%),
      radial-gradient(600px 500px at -10% 60%, rgba(255,122,51,0.08), transparent 60%);
    pointer-events: none;
  }

  .hero-grid{ display:grid; grid-template-columns: 1.15fr 0.85fr; gap: 48px; align-items:center; margin-bottom: 64px; }
  @media (max-width: 960px){ .hero-grid{ grid-template-columns: 1fr; } }

  .hero-visual{ position:relative; }
  .visual-frame{
    position: relative;
    aspect-ratio: 4/5;
    border-radius: 28px;
    overflow: hidden;
    border: 1px solid var(--border);
    background:
      radial-gradient(circle at 30% 22%, rgba(255,122,51,0.35), transparent 55%),
      radial-gradient(circle at 75% 78%, rgba(255,179,122,0.18), transparent 50%),
      var(--bg-elevated);
    display:flex; align-items:center; justify-content:center;
  }
  .visual-frame img{
    width: 100%; height: 100%;
    object-fit: cover;
    transform: scaleX(-1);
  }
  @media (max-width: 480px){
    .visual-frame{ aspect-ratio: 1/1; }
  }

  .reveal{ opacity:0; transform: translateY(26px); transition: opacity .8s var(--ease), transform .8s var(--ease); }
  .reveal.is-visible{ opacity:1; transform:none; }
  @media (prefers-reduced-motion: reduce){ .reveal{ opacity:1; transform:none; transition:none; } }

  nav{
    position: fixed; top:0; left:0; right:0; z-index:50;
    display:flex; justify-content:space-between; align-items:center;
    padding: 22px 6vw;
    backdrop-filter: blur(10px);
    background: rgba(13,19,32,0.6);
    border-bottom: 1px solid var(--border);
  }
  .nav-name{ font-family:'IBM Plex Mono', monospace; font-size:13px; letter-spacing:0.04em; }
  .nav-links{ display:flex; gap:28px; list-style:none; margin:0; padding:0; }
  .nav-links a{ text-decoration:none; font-size:14px; color: var(--ink-muted); transition: color .3s var(--ease); }
  .nav-links a:hover{ color: var(--orange-soft); }
  @media (max-width:720px){ .nav-links{ display:none; } }

  section{ padding: 150px 6vw 90px; position:relative; z-index:2; }

  /* ===== HERO + USP merged block ===== */
  .hero{ padding-top: 130px; padding-bottom: 60px; }
  .hero .eyebrow{ margin-bottom: 22px; }
  .hero .name{ font-size: clamp(52px, 9vw, 120px); line-height: 0.95; margin: 0 0 14px; }
  .hero .role{ font-size: clamp(18px, 2.2vw, 24px); color: var(--orange-soft); margin: 0 0 34px; }
  .hero-desc{ max-width: 620px; font-size: 17px; line-height: 1.65; color: var(--ink-muted); margin: 0 0 56px; }

  .usp-grid{ display:grid; grid-template-columns: repeat(3,1fr); gap: 22px; margin-bottom: 64px; }
  @media (max-width:860px){ .usp-grid{ grid-template-columns:1fr; } }
  .usp-card{
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 26px 24px;
    transition: border-color .3s var(--ease), transform .4s var(--ease);
  }
  .usp-card:hover{ border-color: rgba(255,122,51,0.4); transform: translateY(-4px); }
  .usp-icon{
    width: 60px; height: 60px; border-radius: 16px;
    margin-bottom: 20px;
    display:flex; align-items:center; justify-content:center;
    background: linear-gradient(160deg, rgba(255,122,51,0.22), rgba(255,122,51,0.03));
    border: 1px solid rgba(255,122,51,0.35);
    box-shadow: 0 14px 28px -16px rgba(255,122,51,0.55), inset 0 1px 0 rgba(255,255,255,0.08);
  }
  .usp-icon svg{ width: 28px; height: 28px; }
  .usp-card h3{ font-family:'Bounded',sans-serif; font-weight:400; text-transform:uppercase; font-size:15px; margin:0 0 8px; letter-spacing:0.01em; }
  .usp-card p{ font-size:14px; color: var(--ink-muted); line-height:1.5; margin:0; }

  /* ===== marquee ===== */
  .marquee-wrap{
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 22px 0;
    overflow: hidden;
    white-space: nowrap;
  }
  .marquee-track{
    display: inline-flex;
    gap: 40px;
    animation: scroll-left 26s linear infinite;
  }
  .marquee-track span{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    color: var(--ink-muted);
    letter-spacing: 0.02em;
  }
  .marquee-track span.tool{ color: var(--ink); }
  @keyframes scroll-left{ from{ transform: translateX(0); } to{ transform: translateX(-50%); } }
  @media (prefers-reduced-motion: reduce){ .marquee-track{ animation: none; } }

  /* ===== work ===== */
  .work-head{ display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:20px; margin-bottom:44px; }
  .work-head h2{ font-size: clamp(28px,4vw,42px); margin:10px 0 0; }
  .filters{ display:flex; gap:10px; }
  .filter-btn{
    font-family: Arial, sans-serif; font-size:14px;
    padding: 9px 20px; border-radius:999px; border:1px solid var(--border);
    background: transparent; color: var(--ink-muted); cursor:pointer;
    transition: all .3s var(--ease);
  }
  .filter-btn.active, .filter-btn:hover{ background: var(--orange); color:#1A0F08; border-color: var(--orange); }

  .gallery{ display:grid; grid-template-columns: repeat(3,1fr); gap:20px; }
  @media (max-width:960px){ .gallery{ grid-template-columns: repeat(2,1fr); } }
  @media (max-width:620px){ .gallery{ grid-template-columns: 1fr; } }

  .card{
    position:relative; aspect-ratio:4/5; border-radius: var(--radius); overflow:hidden;
    cursor:pointer; border: 1px solid var(--border);
    transition: transform .5s var(--ease), border-color .4s var(--ease);
  }
  .card:hover{ transform: translateY(-8px); border-color: rgba(255,122,51,0.5); }
  .card .thumb{ position:absolute; inset:0; background-size:cover; background-position:center; }
  .card .overlay{
    position:absolute; inset:0; display:flex; flex-direction:column; justify-content:flex-end;
    padding:22px; background: linear-gradient(180deg, rgba(13,19,32,0) 35%, rgba(13,19,32,0.9) 100%);
    color:#fff; opacity:0; transition: opacity .4s var(--ease);
  }
  .card:hover .overlay{ opacity:1; }
  .card .overlay .cat{ font-family:'IBM Plex Mono',monospace; font-size:11px; color: var(--orange-soft); margin-bottom:6px; }
  .card .overlay h4{ margin:0; font-family:'Bounded',sans-serif; font-weight:400; text-transform:uppercase; font-size:15px; letter-spacing:0.01em; }

  .g1{ background: radial-gradient(circle at 30% 20%, #3a2a1f, #0D1320 70%); }
  .g2{ background: radial-gradient(circle at 70% 30%, #33241a, #0D1320 70%); }
  .g3{ background: radial-gradient(circle at 40% 70%, #402c1c, #0D1320 70%); }
  .g4{ background: radial-gradient(circle at 60% 60%, #35271b, #0D1320 70%); }
  .g5{ background: radial-gradient(circle at 25% 45%, #3d2b1c, #0D1320 70%); }
  .g6{ background: radial-gradient(circle at 75% 75%, #392a1d, #0D1320 70%); }

  /* ===== footer with photo + contact ===== */
  footer{ padding: 100px 6vw 60px; text-align:center; }
  .footer-photo{
    width: 132px; height: 132px; border-radius: 50%;
    margin: 0 auto 30px;
    background: linear-gradient(160deg, var(--bg-elevated), var(--bg-elevated-2));
    border: 1px solid var(--border);
    display:flex; align-items:center; justify-content:center;
  }
  .footer-photo span{ font-family:'IBM Plex Mono',monospace; font-size:10px; color: var(--ink-muted); text-align:center; padding: 0 10px; }
  footer .eyebrow{ margin-bottom: 16px; }
  footer h2{ font-size: clamp(30px,5vw,52px); margin:0 0 30px; }
  .contact-links{ display:flex; justify-content:center; gap:22px; flex-wrap:wrap; margin-bottom:50px; }
  .contact-links a{
    text-decoration:none; font-size:14.5px; padding:12px 24px; border-radius:999px;
    border: 1px solid var(--border); transition: all .3s var(--ease);
  }
  .contact-links a:hover{ background: var(--orange); color:#1A0F08; border-color: var(--orange); }
  .foot-note{ font-family:'IBM Plex Mono',monospace; font-size:12px; color: var(--ink-muted); }
</style>
</head>
<body>

<div class="bg-fx"></div>

<nav>
  <div class="nav-name">ЕЛИЗАВЕТА</div>
  <ul class="nav-links">
    <li><a href="#work">Работы</a></li>
    <li><a href="#contact">Контакты</a></li>
  </ul>
</nav>

<!-- ===== HERO + USP (единый блок) ===== -->
<section class="hero" id="hero">

  <svg width="0" height="0" style="position:absolute">
    <defs>
      <linearGradient id="iconGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#FFD9A8"/>
        <stop offset="100%" stop-color="#FF7A33"/>
      </linearGradient>
    </defs>
  </svg>

  <div class="hero-grid">
    <div class="hero-text">
      <div class="eyebrow reveal">AI-КРЕАТОР &amp; ВЕБ-ДИЗАЙНЕР</div>
      <h1 class="display name reveal">Елизавета</h1>
      <p class="role reveal">AI-креатор &amp; веб-дизайнер</p>

      <p class="hero-desc reveal">
        Создаю контент для бизнеса и блогеров, на создание которого раньше уходили недели.
        Веб-дизайнер с 4-летним опытом и AI-креатор с 2022 года. Нейрофото, нейровидео,
        мультики, анимация, баннеры, инфографика и контент для соцсетей — быстро, красиво,
        с дизайнерским пониманием результата.
      </p>
    </div>

    <div class="hero-visual reveal">
      <div class="visual-frame">
        <img src="./images/hero-taurus.jpg" alt="Огненный телец — символ Елизаветы">
      </div>
    </div>
  </div>

  <div class="usp-grid reveal">
    <div class="usp-card">
      <div class="usp-icon">
        <svg viewBox="0 0 24 24" fill="none"><path d="M12 2l2 5 5 2-5 2-2 5-2-5-5-2 5-2z" fill="url(#iconGrad)"/><path d="M19 15l1 2.5L22.5 18 20 19l-1 2.5L18 19l-2.5-1L18 17.5z" fill="url(#iconGrad)"/></svg>
      </div>
      <h3>Дизайнерский взгляд + ИИ</h3>
      <p>Не просто промт — результат выглядит как профессиональный дизайн.</p>
    </div>
    <div class="usp-card">
      <div class="usp-icon">
        <svg viewBox="0 0 24 24" fill="none"><path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" fill="url(#iconGrad)"/></svg>
      </div>
      <h3>В AI с 2022 года</h3>
      <p>Знаю, какой инструмент даст лучший результат под твою задачу.</p>
    </div>
    <div class="usp-card">
      <div class="usp-icon">
        <svg viewBox="0 0 24 24" fill="none"><rect x="2" y="5" width="15" height="14" rx="2" fill="url(#iconGrad)"/><path d="M17 9.5l5-3v11l-5-3z" fill="url(#iconGrad)"/></svg>
      </div>
      <h3>Полный цикл контента</h3>
      <p>Фото, видео, анимация, соцсети — всё в одних руках.</p>
    </div>
  </div>

  <div class="marquee-wrap reveal">
    <div class="marquee-track">
      <span>Работаю со следующими нейросетями:</span>
      <span class="tool">Nano Banana</span><span>·</span>
      <span class="tool">GPT Image</span><span>·</span>
      <span class="tool">Seedream</span><span>·</span>
      <span class="tool">Kling</span><span>·</span>
      <span class="tool">Seedance</span><span>·</span>
      <span class="tool">Veo</span><span>·</span>
      <span class="tool">Sora</span><span>·</span>
      <span>Работаю со следующими нейросетями:</span>
      <span class="tool">Nano Banana</span><span>·</span>
      <span class="tool">GPT Image</span><span>·</span>
      <span class="tool">Seedream</span><span>·</span>
      <span class="tool">Kling</span><span>·</span>
      <span class="tool">Seedance</span><span>·</span>
      <span class="tool">Veo</span><span>·</span>
      <span class="tool">Sora</span><span>·</span>
    </div>
  </div>
</section>

<!-- ===== WORK ===== -->
<section id="work">
  <div class="work-head reveal">
    <div>
      <div class="eyebrow">Портфолио</div>
      <h2 class="display">Мои работы</h2>
    </div>
    <div class="filters">
      <button class="filter-btn active" data-filter="all">Все</button>
      <button class="filter-btn" data-filter="photo">Фото</button>
      <button class="filter-btn" data-filter="video">Видео</button>
    </div>
  </div>
  <div class="gallery" id="gallery">
    <div class="card reveal" data-cat="photo"><div class="thumb g1"></div><div class="overlay"><div class="cat">AI PHOTO</div><h4>[Название проекта]</h4></div></div>
    <div class="card reveal" data-cat="video"><div class="thumb g2"></div><div class="overlay"><div class="cat">AI VIDEO</div><h4>[Название проекта]</h4></div></div>
    <div class="card reveal" data-cat="photo"><div class="thumb g3"></div><div class="overlay"><div class="cat">AI PHOTO</div><h4>[Название проекта]</h4></div></div>
    <div class="card reveal" data-cat="photo"><div class="thumb g4"></div><div class="overlay"><div class="cat">AI PHOTO</div><h4>[Название проекта]</h4></div></div>
    <div class="card reveal" data-cat="video"><div class="thumb g5"></div><div class="overlay"><div class="cat">AI VIDEO</div><h4>[Название проекта]</h4></div></div>
    <div class="card reveal" data-cat="photo"><div class="thumb g6"></div><div class="overlay"><div class="cat">AI PHOTO</div><h4>[Название проекта]</h4></div></div>
  </div>
</section>

<!-- ===== FOOTER: фото + контакты ===== -->
<footer id="contact">
  <div class="footer-photo reveal"><span>[ВАШЕ ФОТО]</span></div>
  <div class="eyebrow reveal">КОНТАКТЫ</div>
  <h2 class="display reveal">Обсудим твой проект?</h2>
  <div class="contact-links reveal">
    <a href="#">Telegram</a>
    <a href="#">Instagram</a>
    <a href="mailto:hello@example.com">hello@example.com</a>
  </div>
  <div class="foot-note">© 2026 Елизавета · AI Content</div>
</footer>

<script>
  const items = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if(e.isIntersecting){ e.target.classList.add('is-visible'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  items.forEach(i => io.observe(i));

  const buttons = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('#gallery .card');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const f = btn.dataset.filter;
      cards.forEach(c => { c.style.display = (f === 'all' || c.dataset.cat === f) ? '' : 'none'; });
    });
  });

</script>

</body>
</html>
