<template>
  <v-tooltip bottom>
    <template v-slot:activator="{ on, attrs }">
      <img v-if="container.type=='docker'" v-bind="attrs" v-on="on" src="/docker-logo.png" style="height: 1.2rem;">
      <img v-else-if="container.type=='singularity'" v-bind="attrs" v-on="on" src="/singularity-logo.png" style="height: 1.2rem;">
      <img v-else-if="container.type=='generic'" v-bind="attrs" v-on="on" src="/oras-logo.png" style="height: 1.2rem;">
      <v-icon v-bind="attrs" v-on="on" v-else-if="container.type=='mixed'">mdi-folder-multiple</v-icon>
    </template>
    <span>{{ container.type }}</span>
  </v-tooltip>
</template>
<script lang="ts">
import Vue from 'vue';
import { Container } from '@/store/models';

export default Vue.extend({
  props: {
    container: {
      type: Container,
      required: true,
    },
  }
});
</script>