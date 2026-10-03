package com.shelfwise;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
@org.springframework.scheduling.annotation.EnableScheduling
public class ShelfwiseApplication {
    public static void main(String[] args) { SpringApplication.run(ShelfwiseApplication.class, args); }
}
