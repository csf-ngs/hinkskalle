<template>
  <v-toolbar flat class="grey lighten-3">
    <v-toolbar-title>{{title}}</v-toolbar-title>
    <slot></slot>
    <v-spacer></v-spacer>
    <v-icon>mdi-help-circle-outline</v-icon>
  </v-toolbar>
</template>
<script lang="ts">
import Vue from 'vue';

export default Vue.extend({
  name: 'TopBar',
  props: ['title']
});
</script>