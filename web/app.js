// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', function() {
  // 导航栏滚动效果
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  // 移动端菜单
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const mobileMenu = document.createElement('div');
  mobileMenu.className = 'mobile-menu';
  
  // 复制导航链接到移动端菜单
  const navLinks = document.querySelector('.nav-links');
  if (navLinks && mobileMenuBtn) {
    mobileMenu.innerHTML = `
      <nav class="nav-links">
        <a href="#features" class="nav-link">功能</a>
        <a href="#how-it-works" class="nav-link">工作原理</a>
        <a href="#demo" class="nav-link">演示</a>
        <a href="/chat" class="nav-link nav-cta">开始使用</a>
      </nav>
    `;
    
    document.body.appendChild(mobileMenu);
    
    mobileMenuBtn.addEventListener('click', function() {
      mobileMenu.classList.toggle('open');
      
      // 切换按钮图标
      const svg = this.querySelector('svg');
      if (mobileMenu.classList.contains('open')) {
        svg.innerHTML = '<path d="M18 6L6 18M6 6l12 12"></path>';
      } else {
        svg.innerHTML = '<path d="M3 12h18M3 6h18M3 18h18"></path>';
      }
    });
    
    // 点击链接后关闭菜单
    mobileMenu.addEventListener('click', function(e) {
      if (e.target.tagName === 'A') {
        mobileMenu.classList.remove('open');
        const svg = mobileMenuBtn.querySelector('svg');
        svg.innerHTML = '<path d="M3 12h18M3 6h18M3 18h18"></path>';
      }
    });
  }

  // 平滑滚动
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        const offsetTop = targetElement.offsetTop - 80; // 减去导航栏高度
        
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
      }
    });
  });

  // 元素进入视口动画
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // 观察需要动画的元素
  document.querySelectorAll('.feature-card, .workflow-step, .demo-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });

  // 按钮悬停效果
  document.querySelectorAll('.btn, .nav-link').forEach(button => {
    button.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-2px)';
    });
    
    button.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });

  // 卡片悬停效果
  document.querySelectorAll('.feature-card, .workflow-step, .demo-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-4px)';
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });

  // 功能徽章悬停效果
  document.querySelectorAll('.feature-badge').forEach(badge => {
    badge.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-2px)';
    });
    
    badge.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });

  // 页脚链接悬停效果
  document.querySelectorAll('.footer-link-group a').forEach(link => {
    link.addEventListener('mouseenter', function() {
      this.style.transform = 'translateX(6px)';
    });
    
    link.addEventListener('mouseleave', function() {
      this.style.transform = 'translateX(0)';
    });
  });

  // 模拟聊天预览输入
  const chatInput = document.querySelector('.chat-input input');
  const sendBtn = document.querySelector('.send-btn');
  
  if (chatInput && sendBtn) {
    chatInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        const message = this.value.trim();
        if (message) {
          // 模拟发送消息
          this.value = '';
          
          // 这里可以添加发送消息的动画效果
          console.log('发送消息:', message);
        }
      }
    });
    
    sendBtn.addEventListener('click', function() {
      const message = chatInput.value.trim();
      if (message) {
        // 模拟发送消息
        chatInput.value = '';
        
        // 这里可以添加发送消息的动画效果
        console.log('发送消息:', message);
      }
    });
  }

  // 加载动画
  function showLoading(element) {
    if (!element) return;
    
    const loading = document.createElement('div');
    loading.className = 'loading';
    loading.style.margin = '0 auto';
    
    element.appendChild(loading);
    
    return loading;
  }

  // 移除加载动画
  function hideLoading(loadingElement) {
    if (loadingElement && loadingElement.parentNode) {
      loadingElement.parentNode.removeChild(loadingElement);
    }
  }

  // 初始化页面
  function initPage() {
    console.log('TinyRag 页面初始化完成');
    
    // 这里可以添加其他初始化逻辑
  }

  // 调用初始化函数
  initPage();
});

// 页面加载完成后执行
window.addEventListener('load', function() {
  console.log('页面加载完成');
  
  // 这里可以添加页面完全加载后的逻辑
});

// 窗口大小变化时执行
window.addEventListener('resize', function() {
  console.log('窗口大小变化');
  
  // 这里可以添加响应式调整逻辑
});

// 滚动时执行
window.addEventListener('scroll', function() {
  // 这里可以添加滚动相关的逻辑
});