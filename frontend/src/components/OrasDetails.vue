<template>
  <v-container>
      <v-row v-for="tag in manifest.tags" :key="tag">
        <v-col>
          <hsk-text-input :label="'Pull '+tag" :static-value="manifest.pullCmd(tag)"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <hsk-text-input label="Digest" :static-value="digest"></hsk-text-input>
        </v-col>
      </v-row>
      <v-row justify="center">
        <v-col cols="6" class="d-flex justify-center">
          <div>That's all, folks! (don't have more info on oras containers)</div>
        </v-col>
      </v-row>
  </v-container>
</template>
<script lang="ts">
import { Manifest } from '@/store/models'; 
import Vue from 'vue';

export default Vue.extend({
  name: 'OrasDetails',
  props: {
    manifest: {
      type: Manifest,
      required: true,
    },
  },
  computed: {
    digest: function(): string {
      if (!this.manifest.content.layers) {
        return '';
      }
      return this.manifest.content.layers[0].digest || '';
    }
  }
});
</script>