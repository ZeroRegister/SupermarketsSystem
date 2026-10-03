package com.shelfwise;

import jakarta.servlet.http.HttpServletResponse;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.*;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.*;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.*;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.csrf.CsrfTokenRequestAttributeHandler;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@ConfigurationProperties("shelfwise") record ShelfwiseProperties(boolean demoEnabled,String demoPassword,int cacheTtlSeconds) {}

@Configuration
class SecurityConfig {
 @Bean PasswordEncoder passwordEncoder(){return new BCryptPasswordEncoder(12);}
 @Bean UserDetailsService userDetailsService(UserRepository users){return username->users.findByUsername(username).filter(u->u.enabled).map(u->User.withUsername(u.username).password(u.passwordHash).roles(u.role.name()).build()).orElseThrow(()->new UsernameNotFoundException("Account not found or disabled"));}
 @Bean AuthenticationManager authenticationManager(AuthenticationConfiguration c)throws Exception{return c.getAuthenticationManager();}
 @Bean SecurityFilterChain security(HttpSecurity http,UserRefreshFilter refresh)throws Exception {
   CookieCsrfTokenRepository repo=CookieCsrfTokenRepository.withHttpOnlyFalse();
   CsrfTokenRequestAttributeHandler csrfHandler=new CsrfTokenRequestAttributeHandler();
   http.csrf(c->c.csrfTokenRepository(repo).csrfTokenRequestHandler(csrfHandler))
    .authorizeHttpRequests(a->a.requestMatchers("/api/auth/csrf","/api/auth/login","/actuator/health").permitAll()
      .requestMatchers("/api/auth/**").authenticated()
      .requestMatchers(HttpMethod.GET,"/api/settings").authenticated()
      .requestMatchers("/api/users/**","/api/settings/**").hasRole("ADMIN")
      .requestMatchers(HttpMethod.PATCH,"/api/products/*/thresholds").hasAnyRole("ADMIN","MANAGER")
      .requestMatchers(HttpMethod.POST,"/api/products/**","/api/categories/**","/api/suppliers/**").hasRole("ADMIN")
      .requestMatchers(HttpMethod.PUT,"/api/products/**","/api/categories/**","/api/suppliers/**").hasRole("ADMIN")
      .requestMatchers(HttpMethod.DELETE,"/api/products/**","/api/categories/**","/api/suppliers/**").hasRole("ADMIN")
      .requestMatchers("/api/warnings/**","/api/reports/**","/api/dashboard").hasAnyRole("ADMIN","MANAGER")
      .requestMatchers(HttpMethod.POST,"/api/transactions").hasAnyRole("ADMIN","CLERK")
      .anyRequest().authenticated())
    .formLogin(f->f.disable()).httpBasic(b->b.disable())
    .exceptionHandling(e->e.authenticationEntryPoint((req,res,ex)->{res.setStatus(401);res.setContentType("application/json");res.getWriter().write("{\"code\":\"UNAUTHENTICATED\",\"message\":\"Sign in to continue\"}");}).accessDeniedHandler((req,res,ex)->{res.setStatus(403);res.setContentType("application/json");res.getWriter().write("{\"code\":\"FORBIDDEN\",\"message\":\"This role cannot perform that action\"}");}))
    .logout(l->l.logoutUrl("/api/auth/logout").logoutSuccessHandler((req,res,auth)->{res.setStatus(204);}).invalidateHttpSession(true).deleteCookies("JSESSIONID","XSRF-TOKEN"));
   http.addFilterBefore(refresh,org.springframework.security.web.access.intercept.AuthorizationFilter.class);
   return http.build();
 }
}

@org.springframework.stereotype.Component
class UserRefreshFilter extends org.springframework.web.filter.OncePerRequestFilter {
 private final UserRepository users;
 UserRefreshFilter(UserRepository users){this.users=users;}
 @Override protected void doFilterInternal(jakarta.servlet.http.HttpServletRequest req,jakarta.servlet.http.HttpServletResponse res,jakarta.servlet.FilterChain chain)throws java.io.IOException,jakarta.servlet.ServletException {
  var context=org.springframework.security.core.context.SecurityContextHolder.getContext();var current=context.getAuthentication();
  if(current!=null&&current.isAuthenticated()&&!(current instanceof org.springframework.security.authentication.AnonymousAuthenticationToken)){
   var user=users.findByUsername(current.getName()).filter(u->u.enabled);
   if(user.isEmpty()){context.setAuthentication(null);if(req.getSession(false)!=null)req.getSession(false).removeAttribute(org.springframework.security.web.context.HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY);}
   else if(!current.getAuthorities().stream().anyMatch(a->a.getAuthority().equals("ROLE_"+user.get().role.name()))){var refreshed=new org.springframework.security.authentication.UsernamePasswordAuthenticationToken(current.getPrincipal(),current.getCredentials(),org.springframework.security.core.authority.AuthorityUtils.createAuthorityList("ROLE_"+user.get().role.name()));refreshed.setDetails(current.getDetails());context.setAuthentication(refreshed);}
  }
  chain.doFilter(req,res);
 }
}

@RestController @RequestMapping("/api/auth")
class AuthController {
 private final AuthenticationManager auth; private final UserRepository users;
 AuthController(AuthenticationManager auth,UserRepository users){this.auth=auth;this.users=users;}
 @GetMapping("/csrf") Map<String,String> csrf(org.springframework.security.web.csrf.CsrfToken token){return Map.of("token",token.getToken());}
 @PostMapping("/login") UserView login(@jakarta.validation.Valid @RequestBody LoginInput input, jakarta.servlet.http.HttpServletRequest req){
   var authentication=auth.authenticate(UsernamePasswordAuthenticationToken.unauthenticated(input.username(),input.password()));
   var context=org.springframework.security.core.context.SecurityContextHolder.createEmptyContext();context.setAuthentication(authentication);org.springframework.security.core.context.SecurityContextHolder.setContext(context);
   req.getSession(true);req.changeSessionId();
   req.getSession(true).setAttribute(org.springframework.security.web.context.HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY,context);
   return users.findByUsername(authentication.getName()).map(UserView::of).orElseThrow();
 }
 @GetMapping("/me") UserView me(org.springframework.security.core.Authentication authentication){return users.findByUsername(authentication.getName()).map(UserView::of).orElseThrow();}
}
