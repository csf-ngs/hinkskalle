<template>
  <v-container>
    <v-row>
      <v-col>
        <h2>Latest Uploads</h2>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" xl="6" v-for="(up, i) in latest" :key="i">
        <v-card height="100%" outlined raised class="upload" 
            :to="{name: 'ContainerDetails', params: { entity: up.container.entityName, collection: up.container.collectionName, container: up.container.name }}">
          <v-card-title class="d-flex justify-space-between">
            <div class="text-h6">
              {{up.container.fullPath}}
            </div>
            <div>
              <container-type :container="up.container"></container-type>
            </div>
          </v-card-title>
          <v-card-text>
            {{up.container.createdBy}} | {{(up.container.updatedAt || up.container.createdAt) | moment('YYYY-MM-DD HH:mm:ss')}}
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-chip pill 
              class="mr-1" 
              color="pink lighten-4" 
              v-for="tag in up.tags" 
              :key="tag.name" 
              @click.stop.prevent="copyTag(up.container, tag)">
                <v-icon>mdi-content-copy</v-icon>
                {{tag.name | abbreviate(20)}}
            </v-chip>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
<script lang="ts">
import Vue from 'vue';

import { Container, UploadTag } from '../store/models';
import { pullCmd, libraryUrl } from '@/util/pullCmds';
import ContainerType from '@/components/ContainerType.vue';

export default Vue.extend({
  name: 'LatestContainers',
  components: { ContainerType },
  mounted() {
    this.loadLatest();
  },
  computed: {
    latest() {
      return this.$store.getters['containers/latest'];
    },
  },
  methods: {
    loadLatest() {
      this.$store.dispatch('containers/latest')
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    copyTag: function(container: Container, tag: UploadTag) {
      let prom: Promise<any>;
      if (tag.manifestType) {
        prom = this.$copyText(pullCmd({ path: container.fullPath, type: tag.manifestType }, tag.name));
      }
      else if (tag.imageType && tag.imageType === 'singularity') {
        prom = this.$copyText(`singularity pull library://${libraryUrl({ path: container.fullPath }, tag.name)}`)
      }
      else {
        return;
      }
      prom.then(() => this.$store.commit('snackbar/open', "Copied to clipboard."));
    },
  },

});
</script>